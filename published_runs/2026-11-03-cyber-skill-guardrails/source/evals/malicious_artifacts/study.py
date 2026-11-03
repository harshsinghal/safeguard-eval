"""Freeze the candidate set before validation, and all selections before testing."""
import argparse
from .common import *
from .policies import policies

def register(state):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    for task in TASKS:
        for slug in MODELS:write(state/f'policies/{task}/{slug}.json',policies(task,slug))
    paths=[state/'source-manifest.json',state/'data-audit.json',state/'authorization.json']
    paths+=list((state/'data').rglob('*.jsonl'))+list((state/'metadata').rglob('*.jsonl'))+list((state/'policies').rglob('*.json'))
    write(state/'registration.json',dict(created_utc=now(),models=MODELS,encoder=ENCODER,
        selection='per task/model: validation balanced accuracy, macro F1, shorter policy, lexical policy ID',
        sources=sources(),files={str(p.relative_to(state)):digest(p) for p in sorted(paths)},
        test_viewed_for_authoring=False,threshold_tuning=False,ensemble=False))
    print('Registered all inputs, task definitions and selection rules.')

def freeze(state):
    state=Path(state);verify(state)
    if (state/'freeze.json').exists():raise ValueError('Already frozen')
    selected={};summary={};files={}
    for task in TASKS:
        selected[task]={};summary[task]={}
        for slug in MODELS:
            pp=read(state/f'policies/{task}/{slug}.json');ss={}
            for pid,p in pp.items():
                rr=complete(state,slug,task,'validation',pid);ss[pid]=measures(rr)
                rel=f'predictions/{slug}/{task}/validation/{pid}.jsonl';files[rel]=digest(state/rel)
            best=min(pp,key=lambda pid:(-ss[pid]['balanced_accuracy'],-ss[pid]['macro_f1'],len(canonical(pp[pid])),pid))
            selected[task][slug]=best;summary[task][slug]=ss
        for slug in ('tfidf','liquid'):
            rel=f'learned/{slug}/{task}/selection.json';s=read(state/rel);files[rel]=digest(state/rel)
            selected[task][slug]=s['selected'];summary[task][slug]=s['validation']
            for path,h in s['evidence'].items():
                if digest(state/path)!=h:raise ValueError('Changed learned selection evidence')
                files[path]=h
    write(state/'validation-summary.json',summary);files['validation-summary.json']=digest(state/'validation-summary.json')
    write(state/'freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),selected=selected,files=files))
    print(canonical({'selected':selected}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','freeze']);p.add_argument('--state',required=True)
    a=p.parse_args();globals()[a.action](a.state)
