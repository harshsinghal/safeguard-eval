import argparse
import shutil
from .common import *
from .policies import candidates

def register(state, prior):
    state=Path(state);prior=Path(prior)
    if (state/'registration.json').exists(): raise ValueError('Already registered')
    files={};review={}
    for task in TASKS:
        for kind in ('data','metadata'):
            for split in ('fit','validation','test'):
                rel=f'{kind}/{task}/{split}.jsonl';dest=state/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(prior/rel,dest);files[rel]=digest(dest)
        p=state/f'policies/{task}.json';write(p,candidates(read(prior/f'policies/{task}/qwen.json')));files[str(p.relative_to(state))]=digest(p)
        fit=data(state,task,'fit')
        review[task]=[r['id'] for label in ('ALLOW','BLOCK') for r in
            sorted([r for r in fit if r['expected']==label],key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())[:3]]
    write(state/'development-review.json',dict(fitting_ids=review,
        notes='Read fitting examples only. Legitimate API usage, administration and documentation coexist with hidden setup and authority attacks. Some positive code labels need missing package context. Conceptual policy examples are authored, not copied. No behavior labels or synthetic training rows added.'))
    files['development-review.json']=digest(state/'development-review.json')
    write(state/'authorization.json',dict(approved=True,experiment_cap_usd=4.,gpu_max_hourly_usd=.65,auto_terminate_hours=4,
        paid_api=False,unused_prior_benchmark_allocation_usd=11.768416426))
    files['authorization.json']=digest(state/'authorization.json')
    write(state/'registration.json',dict(created_utc=now(),models=MODELS,seeds=SEEDS,files=files,sources=sources(),
        prior_registration_sha256=digest(prior/'registration.json'),prior_freeze_sha256=digest(prior/'freeze.json')))
    verify(state);print('Registered fixed inputs, policies, sources and budget.')

def freeze(state):
    state=Path(state);verify(state)
    if (state/'freeze.json').exists(): raise ValueError('Already frozen')
    selected={};scores={};files={}
    for task in TASKS:
        selected[task]={};scores[task]={};pp=read(state/f'policies/{task}.json')
        for slug in ('qwen4','qwen9'):
            scores[task][slug]={pid:measures(complete(state,slug,task,'validation',pid)) for pid in pp}
            best=min(pp,key=lambda pid:(-scores[task][slug][pid]['balanced_accuracy'],-scores[task][slug][pid]['macro_f1'],len(canonical(pp[pid])),pid))
            selected[task][slug]=best
            for pid in pp:
                rel=f'predictions/{slug}/{task}/validation/{pid}.jsonl';files[rel]=digest(state/rel)
        for embedding in ('jina-v2','jina-code'):
            for kind in ('lr','mlp'):
                slug=embedding+'-'+kind;rel=f'learned/{slug}/{task}/selection.json';s=read(state/rel)
                selected[task][slug]=s['selected'];scores[task][slug]=s.get('aggregate') or s['validation']
                files.update(s['evidence']);files[rel]=digest(state/rel)
    write(state/'validation-summary.json',scores);files['validation-summary.json']=digest(state/'validation-summary.json')
    write(state/'freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),selected=selected,files=files))
    print(canonical(selected))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','freeze']);p.add_argument('--state',required=True);p.add_argument('--prior')
    a=p.parse_args();register(a.state,a.prior) if a.action=='register' else freeze(a.state)
