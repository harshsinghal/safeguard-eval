"""Run frozen policy text through the recipient's unchanged native interface."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import urllib.parse

from evals.policy_transfer.common import (REGISTRY, check_data, digest, now, read,
    settings, sources, validate_freeze, validate_policy, write)
from evals.qwen_policy import run as qwen
from evals.wildguard import run as specialist
from evals.wildguard.metrics import report


def run(slug, policy_path, data, split, out, base='http://127.0.0.1:8000',
        checkpoint=None, freeze=None):
    rows = check_data(data, split)
    spec = read(REGISTRY)['models'][slug]
    adapter, model = spec['adapter'], spec['model']
    policy = validate_policy(read(policy_path))
    if split in ('audit', 'test'):
        validate_freeze(freeze, slug, policy_path, data, split)
    url = urllib.parse.urlsplit(base)
    if url.scheme != 'http' or url.hostname not in ('localhost', '127.0.0.1') or url.username or url.query:
        raise ValueError('Use localhost or an SSH tunnel')
    native = category = None
    ids = []
    if adapter == 'policylm':
        if not checkpoint:
            raise ValueError('Pinned native checkpoint required')
        sys.path.insert(0, str(Path(checkpoint) / 'inference'))
        from policylm_infer import PolicyLM, Policy, Category
        native = PolicyLM.from_pretrained(checkpoint, device='cuda', dtype='bfloat16',
                                         max_batch_rows=1, max_chars=None)
        category = Policy([Category(policy['name'], violation_rule=policy['block'],
            not_violation_rule=policy['allow'], exception_override=policy['precedence'])])
        native.check_policy(category)
    elif adapter == 'shieldstral':
        ids = specialist.score_ids(base, model, adapter)
    else:
        for label in ('A', 'B', ' A', ' B'):
            tokens = specialist.post(base, '/tokenize', dict(model=model, prompt=label,
                                                            add_special_tokens=False))['tokens']
            if len(tokens) == 1:
                ids.extend(tokens)
            elif label in ('A', 'B'):
                raise ValueError('Labels must be single tokens')
        ids = sorted(set(ids))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(created_utc=now(), study='policy-transfer-v1', adapter=adapter,
        model=model, revision=spec['revision'], policy_id=policy['id'],
        policy_sha256=digest(policy_path), dataset_sha256=digest(data),
        split=split, stage=split, ids=[r['id'] for r in rows], sources=sources(),
        settings=settings(adapter), registry_sha256=digest(REGISTRY),
        freeze_sha256=digest(freeze) if freeze else None, input_fields=['prompt'],
        score_token_ids=ids)
    write(out / 'manifest.json', manifest)
    (out / 'policy.json').write_bytes(Path(policy_path).read_bytes())

    def one(case):
        row = {k: v for k, v in case.items() if k != 'prompt'}
        start = time.monotonic()
        if adapter == 'qwen':
            request = qwen.payload(model, policy, case['prompt'], ids)
        elif adapter == 'shieldstral':
            request = specialist.payload(adapter, model, policy, case['prompt'])
            request['logprob_token_ids'] = ids
        else:
            request = dict(prompt=case['prompt'], policy={k: policy[k] for k in
                ('name', 'block', 'allow', 'precedence')})
        response = None
        row['request_sha256'] = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        try:
            if adapter == 'policylm':
                score = float(native.classify(case['prompt'], category).categories[policy['name']].score)
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError('Invalid probability')
                row.update(score=score, prediction='BLOCK' if score >= .5 else 'ALLOW')
                response = dict(score=score)
            else:
                response = specialist.post(base, '/v1/chat/completions', request)
                row.update(qwen.parse(response) if adapter == 'qwen' else specialist.parse(response, adapter))
        except Exception as e:
            row.update(prediction='ERROR', error_type=type(e).__name__)
        row['latency_seconds'] = time.monotonic() - start
        if response and 'usage' in response:
            row['usage'] = response['usage']
        return row, dict(id=case['id'], request=request, response=response)

    started = time.monotonic()
    outputs = []
    with (out / 'predictions.jsonl').open('x') as pred, (out / 'private-raw.jsonl').open('x') as raw:
        with ThreadPoolExecutor(max_workers=1 if native else 32) as pool:
            for row, trace in pool.map(one, rows):
                outputs.append(row)
                pred.write(json.dumps(row) + '\n'); pred.flush()
                raw.write(json.dumps(trace, ensure_ascii=False) + '\n'); raw.flush()
    result = report(outputs)
    result.update(complete=len(outputs) == len(rows), wall_seconds=time.monotonic() - started,
                  output_tokens=sum((r.get('usage') or {}).get('completion_tokens', 0) for r in outputs))
    write(out / 'summary.json', result)
    print(json.dumps(dict(run=out.name, n=len(rows), accuracy=result['accuracy'],
                          errors=result['errors'], seconds=result['wall_seconds'])), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('slug', 'policy', 'data', 'split', 'out'):
        p.add_argument('--' + field, required=True)
    p.add_argument('--checkpoint'); p.add_argument('--freeze')
    a = vars(p.parse_args()); a['policy_path'] = a.pop('policy')
    run(**a)
