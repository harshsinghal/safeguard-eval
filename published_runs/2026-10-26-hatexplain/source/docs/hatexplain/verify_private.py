"""Replay the recorded decision parsers and reconstruct every submitted request."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def verify(state):
    from evals.hatexplain.common import REGISTRY, digest, read, rows, sources
    from evals.hatexplain.policy import native_fields, payload
    from evals.wildguard.run import parse as specialist_parse
    from evals.qwen_policy.run import parse as qwen_parse
    state = Path(state); reg = read(REGISTRY)
    datasets = {split: {r['id']: r for r in rows(state / 'data' / (split + '.jsonl'))}
                for split in ('fit', 'validation', 'test', 'repeat')}
    n = runs = failures = 0
    for manifest in sorted((state / 'runs').glob('*/manifest.json')):
        m = read(manifest); folder = manifest.parent
        if m['sources'] != sources() or m['registry_sha256'] != digest(REGISTRY):
            raise ValueError('Unexpected source identity')
        policy = read(folder / 'policy.json')
        if digest(folder / 'policy.json') != m['policy_sha256']:
            raise ValueError('Run policy bytes changed')
        pred = rows(folder / 'predictions.jsonl'); raw = rows(folder / 'private-raw.jsonl')
        if [r['id'] for r in pred] != m['ids'] or [r['id'] for r in raw] != m['ids']:
            raise ValueError('Prediction/raw population mismatch')
        cases = datasets['repeat' if m['repeat'] else m['split']]
        if set(cases) != set(m['ids']):
            raise ValueError('Dataset population mismatch')
        for row, trace in zip(pred, raw):
            case = cases[row['id']]
            for k, v in case.items():
                if k != 'prompt' and row[k] != v:
                    raise ValueError('Gold/metadata mismatch')
            adapter = m['adapter']; request = trace['request']
            if adapter == 'policylm':
                expected = dict(policy=dict(name=policy['name'], fields=native_fields(policy, m['variant'])), content=case['prompt'])
            else:
                expected = payload(m['model'], adapter, policy, m['variant'], case['prompt'], request['logprob_token_ids'])
            if request != expected:
                raise ValueError('Recorded request does not match policy and content')
            sha = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if sha != row['request_sha256']:
                raise ValueError('Request hash mismatch')
            if row['prediction'] == 'ERROR':
                failures += 1
                if not row.get('error_type'):
                    raise ValueError('Failure lacks an error record')
            else:
                response = trace['response']
                if adapter == 'policylm':
                    value = response['score']
                    result = dict(score=value, prediction='BLOCK' if value >= .5 else 'ALLOW')
                else:
                    result = qwen_parse(response) if adapter == 'qwen' else specialist_parse(response, adapter)
                if result['prediction'] != row['prediction']:
                    raise ValueError('Decision replay mismatch')
                if 'score' in result and not math.isclose(result['score'], row['score'], abs_tol=1e-12, rel_tol=0):
                    raise ValueError('Score replay mismatch')
            n += 1
        runs += 1
    result = dict(runs=runs, observations=n, errors_retained=failures, request_reconstruction='passed',
                  decision_replay='passed', score_absolute_tolerance=1e-12)
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True)
    a=p.parse_args();sys.path.insert(0,str(Path(__file__).resolve().parents[2]));verify(a.state)
