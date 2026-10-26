"""Immutable classifier runs. Final evaluation requires a verified global freeze."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from evals.hatexplain.common import REGISTRY, digest, now, read, rows, sources, write
from evals.hatexplain.metrics import report
from evals.hatexplain.policy import components, native_fields, payload, render
from evals.wildguard.run import post, score_ids, parse as specialist_parse
from evals.qwen_policy.run import parse as qwen_parse


def verify_freeze(state, model, policy, variant, data, repeat):
    freeze = read(Path(state) / 'freeze.json')
    if freeze['sources'] != sources() or freeze['registry_sha256'] != digest(REGISTRY):
        raise ValueError('Changed implementation or registry after freeze')
    identity = dict(model=model, policy_id=policy['id'], variant=variant, repeat=repeat)
    if identity not in freeze['jobs']:
        raise ValueError('Unregistered test condition')
    if freeze['policy_hashes'][policy['id']] != digest(Path(state) / 'policies' / (policy['id'] + '.json')):
        raise ValueError('Policy changed after freeze')
    expected = read(REGISTRY)['data_hashes']['repeat' if repeat else 'test']
    if digest(data) != expected:
        raise ValueError('Changed test population')


def run(state, slug, policy_path, variant, split, out, checkpoint=None, repeat=False):
    state, out = Path(state), Path(out)
    reg, policy = read(REGISTRY), read(policy_path)
    spec = reg['models'][slug]; adapter = spec['adapter']; model = spec['model']
    data = state / 'data' / (('repeat' if repeat else split) + '.jsonl')
    if split == 'test':
        verify_freeze(state, slug, policy, variant, data, repeat)
    if digest(data) != reg['data_hashes']['repeat' if repeat else split]:
        raise ValueError('Unregistered data')
    cases = rows(data)
    if len({r['id'] for r in cases}) != len(cases) or {r['split'] for r in cases} != {split}:
        raise ValueError('Population mismatch')
    if out.exists():
        raise ValueError('Run directory already exists')
    ids, native, category = [], None, None
    base = 'http://127.0.0.1:8000'
    native_check = None
    if adapter == 'policylm':
        sys.path.insert(0, str(Path(checkpoint) / 'inference'))
        from policylm_infer import PolicyLM, Policy, Category
        native = PolicyLM.from_pretrained(checkpoint, device='cuda', dtype='bfloat16',
                                         max_batch_rows=1, max_chars=None)
        fields = native_fields(policy, variant)
        category = Policy([Category(policy['name'], **fields)])
        native_check = native.check_policy(category)
        rendered = dict(name=policy['name'], fields=fields)
    else:
        if adapter == 'shieldstral':
            ids = score_ids(base, model, adapter)
        else:
            for label in ('A', 'B', ' A', ' B'):
                tok = post(base, '/tokenize', dict(model=model, prompt=label, add_special_tokens=False))['tokens']
                if len(tok) == 1:
                    ids += tok
                elif label in ('A', 'B'):
                    raise ValueError('Classification labels must be single tokens')
            ids = sorted(set(ids))
        rendered = payload(model, adapter, policy, variant, '[SUBMITTED POST]', ids)
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(created_utc=now(), model=model, slug=slug, adapter=adapter, revision=spec['revision'],
        split=split, repeat=repeat, policy_id=policy['id'], policy_sha256=digest(policy_path), variant=variant,
        dataset_sha256=digest(data), ids=[r['id'] for r in cases], sources=sources(), registry_sha256=digest(REGISTRY),
        settings=reg['settings'], components={k: [c['id'] for c in v] for k, v in components(policy, variant).items()},
        native_check=repr(native_check) if native_check is not None else None,
        freeze_sha256=digest(state / 'freeze.json') if split == 'test' else None)
    write(out / 'manifest.json', manifest); write(out / 'policy.json', policy)
    write(out / 'rendered-policy.json', rendered)

    def one(case):
        row = {k: v for k, v in case.items() if k != 'prompt'}
        start = time.monotonic()
        request = dict(policy=rendered, content=case['prompt']) if native else payload(model, adapter, policy, variant, case['prompt'], ids)
        row['request_sha256'] = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        response = None
        try:
            if native:
                value = float(native.classify(case['prompt'], category).categories[policy['name']].score)
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('Invalid probability')
                row.update(score=value, prediction='BLOCK' if value >= .5 else 'ALLOW')
                response = dict(score=value)
            else:
                response = post(base, '/v1/chat/completions', request)
                row.update(qwen_parse(response) if adapter == 'qwen' else specialist_parse(response, adapter))
        except Exception as error:
            row.update(prediction='ERROR', error_type=type(error).__name__)
        row['latency_seconds'] = time.monotonic() - start
        if response and 'usage' in response:
            row['usage'] = response['usage']
        return row, dict(id=case['id'], request=request, response=response)

    start = time.monotonic(); predictions = []
    with (out / 'predictions.jsonl').open('x') as pred, (out / 'private-raw.jsonl').open('x') as raw:
        with ThreadPoolExecutor(max_workers=1 if native else 32) as pool:
            for row, trace in pool.map(one, cases):
                predictions.append(row)
                pred.write(json.dumps(row) + '\n'); pred.flush()
                raw.write(json.dumps(trace, ensure_ascii=False) + '\n'); raw.flush()
    result = report(predictions)
    result.update(complete=len(predictions) == len(cases), wall_seconds=time.monotonic()-start,
                  max_prompt_tokens=max((r.get('usage', {}).get('prompt_tokens', 0) for r in predictions), default=0))
    write(out / 'summary.json', result)
    print(json.dumps(dict(run=out.name, n=result['n'], accuracy=result['accuracy'], macro_f1=result['macro_f1'],
                          errors=result['errors'], seconds=result['wall_seconds'])), flush=True)
    if result['errors'] > max(2, .01*len(cases)):
        raise RuntimeError('Excess inference failures; preserve this attempt and inspect before continuing')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for arg in ('state', 'slug', 'policy-path', 'variant', 'split', 'out'):
        p.add_argument('--' + arg, required=True)
    p.add_argument('--checkpoint'); p.add_argument('--repeat', action='store_true')
    run(**vars(p.parse_args()))
