"""Identities, fixed protocol constants, and strict feature alignment."""
from pathlib import Path
import numpy as np
from evals.ensemble.common import read, rows, write, write_rows, digest, now, assert_disjoint

ROOT = Path(__file__).resolve().parents[2]
MODELS = {
    'qwen': dict(model='Qwen/Qwen3.5-4B', revision='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a',
                 layers=[16, 24, 32], poolings=['mean', 'last'], width=2560),
    'shieldstral': dict(model='mistralai/Shieldstral-1.0-3B', revision='003ec7e2b0bab5f0e6307edbaf186fa5822b76f5',
                    layers=[13, 20, 26], poolings=['last', 'mean'], width=3072),
}
CS = [0.0001, 0.001, 0.01, 0.1, 1.0]
PRIMARY = {'qwen': 'qwen-l32-mean', 'shieldstral': 'shieldstral-l26-last'}


def source_hashes():
    pp = list((ROOT/'evals/shield_probe').glob('*.py'))
    pp += [ROOT/'evals/leaderboard/metrics.py', ROOT/'evals/qwen_policy/run.py',
           ROOT/'evals/wildguard/run.py', ROOT/'evals/wildguard/metrics.py', ROOT/'evals/run.py',
           ROOT/'evals/ensemble/common.py', ROOT/'docs/shield-probe/PLAN.md']
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
    if manifest.get('sources') != source_hashes():raise ValueError('Feature code differs from current registration')
    if manifest.get('policy_sha256') != digest(Path(state)/'policy.json'):raise ValueError('Feature policy changed')
    if manifest.get('model') != MODELS[model]:raise ValueError('Feature model changed')
    for name,h in manifest['artifacts'].items():
        if digest(folder/name)!=h:raise ValueError('Feature artifact changed: '+name)
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
