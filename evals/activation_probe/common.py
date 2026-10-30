"""Identities, fixed protocol constants, and strict feature alignment."""
from pathlib import Path
import numpy as np
from evals.ensemble.common import read, rows, write, write_rows, digest, now, assert_disjoint

ROOT = Path(__file__).resolve().parents[2]
MODELS = {
    'qwen': dict(model='Qwen/Qwen3.5-0.8B', revision='2fc06364715b967f1860aea9cf38778875588b17',
                 layers=[12, 18, 24], poolings=['mean', 'last'], width=1024),
    'policylm': dict(model='musubilabs/policylm-1.7b', revision='b3b2cd408a08a68ab6a30c1fc1e440204e44d57e',
                    layers=[14, 21, 28], poolings=['slot', 'mean'], width=2048),
}
CS = [0.0001, 0.001, 0.01, 0.1, 1.0]
PRIMARY = {'qwen': 'qwen-l24-mean', 'policylm': 'policylm-l28-slot'}


def source_hashes():
    pp = list((ROOT/'evals/activation_probe').glob('*.py'))
    pp += [ROOT/'evals/leaderboard/metrics.py', ROOT/'evals/qwen_policy/run.py',
           ROOT/'evals/ensemble/common.py', ROOT/'docs/activation-probe/PLAN.md']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(pp)}


def keys(model):
    s = MODELS[model]
    return [f'{model}-l{layer}-{pool}' for layer in s['layers'] for pool in s['poolings']]


def labels(metadata):
    if any(r['expected'] not in ('ALLOW', 'BLOCK') for r in metadata):
        raise ValueError('Invalid target')
    return np.asarray([r['expected'] == 'BLOCK' for r in metadata], dtype=int)


def load_features(state, model, split):
    folder = Path(state)/'features'/model/split
    manifest = read(folder/'manifest.json')
    meta = rows(Path(state)/'metadata'/(split+'.jsonl.gz'))
    if manifest['ids'] != [r['id'] for r in meta]:
        raise ValueError('Feature order does not match metadata')
    if manifest['metadata_sha256'] != digest(Path(state)/'metadata'/(split+'.jsonl.gz')):
        raise ValueError('Feature metadata changed')
    features = {}
    for key in keys(model):
        p = folder/(key+'.npy')
        if digest(p) != manifest['artifacts'][p.name]:
            raise ValueError('Feature artifact changed')
        a = np.load(p, allow_pickle=False)
        if a.shape != (len(meta), MODELS[model]['width']):
            raise ValueError('Invalid feature shape')
        features[key] = a
    valid = np.asarray(manifest['valid'], dtype=bool)
    if valid.shape != (len(meta),) or any(not np.isfinite(a[valid]).all() for a in features.values()):
        raise ValueError('Invalid finite-feature mask')
    return meta, features, valid, manifest


def matrix(features, representation):
    arrays = [features[k] for k in representation]
    if len({a.shape[0] for a in arrays}) != 1:
        raise ValueError('Feature populations differ')
    return np.concatenate(arrays, axis=1).astype(np.float64)


def content_mask(offsets, start, end):
    """Tokens overlapping content, excluding zero-length special/padding spans."""
    return np.asarray([b > a and b > start and a < end for a, b in offsets], dtype=bool)
