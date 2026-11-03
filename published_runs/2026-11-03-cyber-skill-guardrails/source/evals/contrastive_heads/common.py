from pathlib import Path
import numpy as np
from evals.ensemble.common import read, rows, write, write_rows, digest, now, assert_disjoint

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ['wildguard', 'hatexplain']
BACKENDS = ['policylm', 'modernbert']
SEEDS = [20261031, 20261101, 20261102]
CS = [.0001, .001, .01, .1, 1.]
DECAYS = [.001, .01]
EPOCHS = [5, 10, 20]
MODELS = {
    'policylm': dict(model='musubilabs/policylm-1.7b', revision='b3b2cd408a08a68ab6a30c1fc1e440204e44d57e', width=2048),
    'modernbert': dict(model='answerdotai/ModernBERT-base', revision='8949b909ec900327062f0ebf497f51aef5e6f0c8', width=768),
}

def sources():
    paths = list((ROOT/'evals/contrastive_heads').glob('*.py'))
    paths += [ROOT/p for p in ['evals/activation_probe/extract.py','evals/activation_probe/common.py',
        'evals/hatexplain/policy.py','evals/ensemble/common.py','evals/leaderboard/metrics.py',
        'docs/contrastive-heads/PLAN.md']]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}

def labels(meta):
    if any(r['expected'] not in ['ALLOW','BLOCK'] for r in meta):
        raise ValueError('Unknown target')
    return np.asarray([r['expected']=='BLOCK' for r in meta], dtype=np.int64)

def load(state, ds, backend, split):
    state = Path(state); folder = state/'features'/ds/backend/split
    m = read(folder/'manifest.json'); meta = rows(state/'metadata'/ds/(split+'.jsonl.gz'))
    if m['ids'] != [r['id'] for r in meta] or m['metadata_sha256'] != digest(state/'metadata'/ds/(split+'.jsonl.gz')):
        raise ValueError('Feature/metadata identity mismatch')
    for n,h in m['artifacts'].items():
        if digest(folder/n) != h: raise ValueError('Changed feature artifact')
    x = np.load(folder/'features.npy', allow_pickle=False)
    if x.shape != (len(meta), MODELS[backend]['width']) or not np.isfinite(x).all():
        raise ValueError('Invalid features; do not silently drop cases')
    return meta, x, m

def check_registration(state):
    state = Path(state); r = read(state/'registration.json')
    if r['sources'] != sources(): raise ValueError('Registered source changed')
    for p,h in r['data_hashes'].items():
        if digest(state/p) != h: raise ValueError('Registered data changed: '+p)
    return r

def check_freeze(state):
    state=Path(state); check_registration(state); f=read(state/'freeze.json')
    if f['sources']!=sources(): raise ValueError('Frozen source changed')
    for p,h in f['hashes'].items():
        if digest(state/p)!=h: raise ValueError('Frozen artifact changed: '+p)
    return f
