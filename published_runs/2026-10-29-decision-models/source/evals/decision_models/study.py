"""Register, author on fitting data, and freeze decisions on validation only."""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np

from evals.ensemble.common import assert_disjoint, digest, now, read, rows
from evals.jev.api import canonical, save
from evals.jev.study import DATA, IDS, base_policies, choose_examples, read_data
from evals.leaderboard.metrics import select

ROOT = Path(__file__).resolve().parents[2]
MODELS = {
    'kev': dict(id='jaredpalmer/kev-4b', revision='6cfce5c2fa4b4bd64026336ab649c5ca78857d52',
                code_revision='2074cc44256200bb37540103fa4572901faa10f3', dtype='bfloat16',
                base='Qwen/Qwen3.5-4B-Base', base_revision='1001bb4d826a52d1f399e183466143f4da7b741b'),
    'clef': dict(id='Cloudflare/clef-flash', revision='f0b7d3cd65296abfe459e6c228b618f5d8b26d2f', dtype='bfloat16')}


def sources():
    pp = [ROOT/'evals/decision_models'/n for n in ('study.py','adapters.py','infer.py','vendor-hashes.json')]
    pp += [ROOT/p for p in ('evals/jev/study.py', 'evals/jev/api.py', 'evals/ensemble/common.py',
                            'evals/leaderboard/metrics.py', 'docs/decision-models/PLAN.md')]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(pp)}


def prepare(state, data):
    state = Path(state)
    if (state/'registration.json').exists():
        raise ValueError('Already registered')
    manifest = {}
    for ds in DATA:
        parts = []
        manifest[ds] = {}
        for split in ('fit', 'validation', 'test'):
            dest = state/'data'/ds/(split+'.jsonl')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(data)/ds/(split+'.jsonl'), dest)
            rr = read_data(state, ds, split)
            parts.append(rr)
            manifest[ds][split] = dict(n=len(rr), sha256=digest(dest))
        assert_disjoint(*parts)
        save(state/'policies'/ds/'initial.json', base_policies(ds))
    shutil.copy2(ROOT/'docs/decision-models/PLAN.md', state/'PLAN.md')
    save(state/'registration.json', dict(created_utc=now(), models=MODELS, data=manifest, sources=sources(),
        initial_hashes={ds:digest(state/'policies'/ds/'initial.json') for ds in DATA}))


def verify(state):
    r = read(Path(state)/'registration.json')
    if r['sources'] != sources():
        raise ValueError('Registered implementation changed; amend before continuing')
    for ds, h in r['initial_hashes'].items():
        if digest(Path(state)/'policies'/ds/'initial.json') != h:
            raise ValueError('Initial policy changed')
    return r


def pred_path(state, slug, ds, split, pid):
    return Path(state)/'runs'/slug/ds/split/(pid+'.jsonl')


def predictions(state, slug, ds, split, pid):
    expected = {r['id']:r for r in read_data(state, ds, split)}
    rr = rows(pred_path(state, slug, ds, split, pid))
    if len(rr) != len(expected) or {r['id'] for r in rr} != set(expected):
        raise ValueError('Missing or duplicate predictions')
    for r in rr:
        if any(r[k] != expected[r['id']][k] for k in ('expected','split','group','prompt_sha256')):
            raise ValueError('Prediction population mismatch')
    return sorted(rr, key=lambda r:r['id'])


def author(state, slug):
    state = Path(state); verify(state)
    marker = state/slug/'policies-freeze.json'
    if marker.exists():
        raise ValueError('Already authored')
    hashes, fit = {}, {}
    for ds in DATA:
        pp = read(state/'policies'/ds/'initial.json')
        chosen = choose_examples(read_data(state, ds, 'fit'), predictions(state,slug,ds,'fit','detailed'))
        pp['examples'] = copy.deepcopy(pp['detailed'])
        pp['examples']['instructions'] += '\n\nLabeled examples illustrating this policy:\n' + '\n'.join(
            canonical({'content':r['prompt'],'classification':r['expected']}) for r in chosen)
        dest = state/'policies'/slug/ds/'final.json'
        save(dest, pp); save(dest.parent/'examples-provenance.json', chosen)
        hashes[str(dest.relative_to(state))] = digest(dest)
        p = pred_path(state,slug,ds,'fit','detailed'); fit[str(p.relative_to(state))] = digest(p)
    save(marker, dict(created_utc=now(), sources=sources(), policies=hashes, fitting=fit))


def verify_policies(state, slug):
    state = Path(state); verify(state)
    f = read(state/slug/'policies-freeze.json')
    if f['sources'] != sources():
        raise ValueError('Source changed after policy freeze')
    for p,h in {**f['policies'],**f['fitting']}.items():
        if digest(state/p) != h:
            raise ValueError('Frozen policy or fitting evidence changed')
    return f


def candidates(preds):
    return {p:dict(prediction=np.array([{'ALLOW':0,'BLOCK':1,'ERROR':-1}[r['prediction']] for r in rr]),
                   score=np.array([r['score'] if r['score'] is not None else np.nan for r in rr]))
            for p,rr in preds.items()}


def freeze(state):
    state = Path(state); verify(state)
    if (state/'freeze.json').exists():
        raise ValueError('Already frozen')
    selections, evidence, per_policy = {}, {}, {}
    for slug in MODELS:
        verify_policies(state,slug)
        for ds in DATA:
            pp = {pid:predictions(state,slug,ds,'validation',pid) for pid in IDS}
            y = np.array([int(r['expected']=='BLOCK') for r in pp['brief']])
            cc = candidates(pp)
            chosen, grid = select(y,cc)
            selections[slug+'/'+ds] = chosen
            per_policy[slug+'/'+ds] = {pid:select(y,{pid:c})[0] for pid,c in cc.items()}
            save(state/'selection-grid'/slug/(ds+'.json'), grid)
            for pid in IDS:
                p = pred_path(state,slug,ds,'validation',pid); evidence[str(p.relative_to(state))] = digest(p)
    save(state/'freeze.json',dict(created_utc=now(),sources=sources(),selections=selections,
        per_policy=per_policy,validation_hashes=evidence,registration_sha256=digest(state/'registration.json'),
        policy_freeze_hashes={s:digest(state/s/'policies-freeze.json') for s in MODELS}))
    print(json.dumps(selections,indent=2))


def verify_freeze(state):
    state = Path(state); verify(state)
    f = read(state/'freeze.json')
    if f['sources'] != sources() or f['registration_sha256'] != digest(state/'registration.json'):
        raise ValueError('Freeze source mismatch')
    for s,h in f['policy_freeze_hashes'].items():
        verify_policies(state,s)
        if digest(state/s/'policies-freeze.json') != h: raise ValueError('Policy freeze changed')
    for p,h in f['validation_hashes'].items():
        if digest(state/p) != h: raise ValueError('Validation outputs changed')
    return f


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['prepare','author','freeze'])
    ap.add_argument('--state',required=True); ap.add_argument('--data'); ap.add_argument('--model',choices=MODELS)
    a=ap.parse_args()
    if a.action=='prepare': prepare(a.state,a.data)
    elif a.action=='author': author(a.state,a.model)
    else: freeze(a.state)

if __name__=='__main__': main()
