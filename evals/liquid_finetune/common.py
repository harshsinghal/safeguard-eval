from pathlib import Path
import hashlib
import numpy as np
from evals.ensemble.common import read, rows, write, write_rows, digest, now, assert_disjoint

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'LiquidAI/LFM2.5-Encoder-350M'
REVISION = 'b886781f7c6f10ca9b7096e21b83e30a073c2f39'
SEEDS = [20261031, 20261101, 20261102]
RATES = [2e-5, 5e-5]
CS = [.0001, .001, .01, .1, 1.]
EPOCHS = 3
MAX_LENGTH = 8192
PROFILES = ['accuracy', 'balanced', 'false_block_limit', 'catch_target']


def sources():
    paths = list((ROOT/'evals/liquid_finetune').glob('*.py'))
    paths += [ROOT/p for p in ['evals/ensemble/common.py', 'evals/leaderboard/metrics.py',
                              'docs/liquid-finetune/PLAN.md']]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def labels(meta):
    if any(r['expected'] not in ['ALLOW', 'BLOCK'] for r in meta):
        raise ValueError('Unknown target')
    return np.asarray([r['expected'] == 'BLOCK' for r in meta], dtype=np.int64)


def check_registration(state, test=False):
    state = Path(state); r = read(state/'registration.json')
    if r['sources'] != sources():
        raise ValueError('Registered source changed')
    for p,h in r['data_hashes'].items():
        if not test and Path(p).name.startswith('test.'):
            continue
        # Test metadata never needs to be on the GPU.
        if test and p == 'metadata/test.jsonl.gz' and not (state/p).exists():
            continue
        if digest(state/p) != h:
            raise ValueError('Registered data changed: '+p)
    return r


def load_inputs(state, split):
    state = Path(state); data = rows(state/'inputs'/(split+'.jsonl'))
    ids = [r['id'] for r in data]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate inputs')
    for r in data:
        if hashlib.sha256(r['prompt'].encode()).hexdigest() != r['prompt_sha256']:
            raise ValueError('Changed prompt')
    return data


def aligned_metadata(state, split, ids=None):
    meta = rows(Path(state)/'metadata'/(split+'.jsonl.gz'))
    if ids is not None and ids != [r['id'] for r in meta]:
        raise ValueError('Metadata ordering changed')
    labels(meta)
    return meta


def check_freeze(state, checkpoints=False):
    state = Path(state); check_registration(state)
    f = read(state/'freeze.json')
    if f['sources'] != sources() or f['registration_sha256'] != digest(state/'registration.json'):
        raise ValueError('Frozen sources/registration changed')
    for p,h in f['hashes'].items():
        if digest(state/p) != h:
            raise ValueError('Frozen artifact changed: '+p)
    if checkpoints:
        for p,h in f['selected_checkpoints'].items():
            if digest(state/p) != h:
                raise ValueError('Selected weights changed: '+p)
    return f
