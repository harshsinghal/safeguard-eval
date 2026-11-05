import copy
from pathlib import Path
from evals.prompt_injection.common import canonical, hash_value, digest, now, read, write, rows, jsonl, measures
from evals.prompt_injection.common import MODELS as PREVIOUS_MODELS

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261104
TASKS = ('action', 'trajectory')
SPLITS = ('fit', 'validation', 'test')
MODELS = copy.deepcopy(PREVIOUS_MODELS)
MODELS['safeguard']['provider'] = 'self-hosted; provider recorded in runtime manifest'
MODEL_NAMES = tuple(MODELS)
PRIMARY = ('shieldstral', 'safeguard', 'jev', 'kev', 'clef')
DATA_REVISION = 'aadeae009800d8fbcd145575f1d1a6b37abb0950'
DATA_SHA256 = '6429dc6f958e2b1fe242f2528dc6087c62e60e903263cf57dd88bc949752c90d'


def metadata(row):
    return {k: v for k, v in row.items() if k not in ('prompt', 'user_request', 'actor_text')}


def data(state, task, split, model=None):
    rr = rows(Path(state)/f'data/{task}/{split}.jsonl')
    if len({r['id'] for r in rr}) != len(rr):
        raise ValueError('Duplicate input IDs')
    for r in rr:
        if hash_value(r['prompt']) != r['prompt_sha256']:
            raise ValueError('Input hash mismatch')
    if model is not None:
        eligible = set(read(Path(state)/'eligibility.json')['policylm' if model == 'policylm' else 'primary'])
        rr = [r for r in rr if r['id'] in eligible]
    return rr


def sources():
    pp = list((ROOT/'evals/stepguard').glob('*.py'))
    pp += [ROOT/p for p in (
        'evals/prompt_injection/common.py', 'evals/prompt_injection/infer.py',
        'evals/retrieved_examples/native.py', 'evals/retrieved_examples/common.py',
        'evals/decision_models/adapters.py', 'evals/decision_models/study.py',
        'evals/decision_models/vendor-hashes.json', 'evals/jev/api.py',
        'evals/leaderboard/metrics.py', 'evals/run.py',
        'docs/security-cognition/STEPGUARD-RUN-PLAN.md')]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(pp)}


def verify(state, test=False):
    state = Path(state)
    reg = read(state/'registration.json')
    if reg['sources'] != sources():
        raise ValueError('Registered source changed; record an amendment')
    for rel, checksum in reg['files'].items():
        if not test and '/test.' in rel:
            continue
        if digest(state/rel) != checksum:
            raise ValueError('Registered file changed: '+rel)
    if test:
        freeze = read(state/'freeze.json')
        if freeze['registration_sha256'] != digest(state/'registration.json'):
            raise ValueError('Selection registration mismatch')
        for rel, checksum in freeze['files'].items():
            if digest(state/rel) != checksum:
                raise ValueError('Selection evidence changed: '+rel)
    return reg


def complete(state, model, task, split, pid):
    expected = {r['id']: r for r in data(state, task, split, model)}
    rr = rows(Path(state)/f'predictions/{model}/{task}/{split}/{pid}.jsonl')
    if len(rr) != len(expected) or {r['id'] for r in rr} != set(expected):
        raise ValueError('Incomplete prediction population')
    for r in rr:
        if any(r[k] != expected[r['id']][k] for k in ('expected', 'group', 'prompt_sha256', 'split')):
            raise ValueError('Misaligned prediction')
        if r['prediction'] not in ('ALLOW', 'BLOCK', 'ERROR'):
            raise ValueError('Invalid decision')
    return sorted(rr, key=lambda r: r['id'])
