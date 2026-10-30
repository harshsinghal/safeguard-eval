from pathlib import Path
import numpy as np
from evals.ensemble.common import read, rows, write, write_rows, digest, now, assert_disjoint
from evals.shield_probe.common import MODELS

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261030
POLICIES = ['p0', 'p1', 'p2', 'p3', 'p4']


def sources():
    files = list((ROOT/'evals/policy_corrections').glob('*.py'))
    files += [ROOT/p for p in ['evals/ensemble/common.py','evals/shield_probe/common.py',
        'evals/leaderboard/metrics.py','evals/qwen_policy/run.py','evals/wildguard/run.py',
        'evals/wildguard/metrics.py','evals/wildguard/data.py','evals/run.py',
        'docs/policy-corrections/PLAN.md']]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}


def labels(metadata):
    if any(r['expected'] not in ('ALLOW','BLOCK') for r in metadata):raise ValueError('Bad label')
    return np.array([r['expected']=='BLOCK' for r in metadata],dtype=int)


def check_registration(state):
    state=Path(state);r=read(state/'registration.json')
    if r['sources']!=sources():raise ValueError('Code changed after registration')
    for p,h in r['artifacts'].items():
        if digest(state/p)!=h:raise ValueError('Registered artifact changed: '+p)
    return r


def output_path(state,model,policy,split):
    return Path(state)/'outputs'/model/policy/(split+'.json')


def load_output(state,model,policy,split):
    state=Path(state);o=read(output_path(state,model,policy,split))
    m=rows(state/'metadata'/(split+'.jsonl.gz'))
    if o['ids']!=[r['id'] for r in m]:raise ValueError('Output identity/order mismatch')
    if o['metadata_sha256']!=digest(state/'metadata'/(split+'.jsonl.gz')):raise ValueError('Metadata changed')
    if o['policy_sha256']!=digest(state/'policies'/(policy+'.json')):raise ValueError('Policy changed')
    if o['model']!=MODELS[model] or o['sources']!=sources():raise ValueError('Model or source changed')
    if o['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Registration changed')
    if split in ('holdout','test') and o['freeze_sha256']!=digest(state/'freeze.json'):raise ValueError('Final inference preceded freeze')
    manifest=read(state/'data-manifest.json')
    inp=('sealed-inputs' if split in ('holdout','test') else 'inputs')+'/'+split+'.jsonl'
    if o['input_sha256']!=manifest['hashes'][inp]:raise ValueError('Input identity changed')
    scores=o['scores']
    if o['ids']!=[r['id'] for r in o['records']] or scores!=[r['score'] for r in o['records']]:raise ValueError('Score record mismatch')
    if len(scores)!=len(m):raise ValueError('Output length mismatch')
    if any(s is not None and (not np.isfinite(s) or not 0<=s<=1) for s in scores):raise ValueError('Invalid score')
    return m,dict(score=scores,prediction=[-1 if s is None else int(s>=.5) for s in scores])
