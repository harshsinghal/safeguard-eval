import argparse
from .common import *
from .policies import policies

def register(state):
    from evals.jev.api import payload
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    review={};sizes={}
    for task in TASKS:
        for slug in MODELS:write(state/f'policies/{task}/{slug}.json',policies(task,slug))
        fit=data(state,task,'fit');review[task]=[r['id'] for label in ('ALLOW','BLOCK') for r in sorted([r for r in fit if r['expected']==label],key=lambda r:hash_value([SEED,r['id']]))[:3]]
        # Mechanical label-blind request-bound audit; no test inference or review.
        for split in ('fit','validation','test'):
            sizes[task+'/'+split]=max(len(canonical(payload(r['prompt'],{'moderation':p})).encode()) for r in data(state,task,split) for p in policies(task,'jev').values())
    write(state/'development-review.json',dict(ids=review,scope='Only these fitting examples may be inspected for authoring. No test-derived edits.'))
    write(state/'request-size-audit.json',sizes)
    write(state/'authorization.json',dict(approved=True,experiment_cap_usd=6.,gpu_cap_usd=4.,jev_cap_usd=2.,gpu_max_hourly_usd=.65,auto_terminate_hours=4,unused_prior_benchmark_allocation_usd=11.168416426,scope='CyberSecEval request classification and MalSkillBench complete-text package screening.'))
    pp=[state/p for p in ('authorization.json','data-audit.json','source-manifest.json','package-manifest.jsonl','development-review.json','request-size-audit.json')]
    pp+=list((state/'data').rglob('*.jsonl'))+list((state/'metadata').rglob('*.jsonl'))+list((state/'policies').rglob('*.json'))
    write(state/'registration.json',dict(created_utc=now(),models=MODELS,embedding=EMBEDDING,seeds=SEEDS,files={str(p.relative_to(state)):digest(p) for p in sorted(pp)},sources=sources(),test_viewed_for_authoring=False,threshold_search=False,ensemble=False))
    verify(state);print('Registered inputs, policies, interfaces and budget.')

def freeze(state):
    state=Path(state);verify(state)
    if (state/'freeze.json').exists():raise ValueError('Already frozen')
    selected={};summary={};files={}
    for task in TASKS:
        selected[task]={};summary[task]={}
        for slug in MODELS:
            pp=read(state/f'policies/{task}/{slug}.json');ss={}
            for pid in pp:
                rr=complete(state,slug,task,'validation',pid);ss[pid]=measures(rr)
                path=f'predictions/{slug}/{task}/validation/{pid}.jsonl';files[path]=digest(state/path)
            choices=['native'] if slug=='promptguard' else ['brief','structured','contrasts']
            best=min(choices,key=lambda pid:(-ss[pid]['balanced_accuracy'],-ss[pid]['macro_f1'],len(canonical(pp[pid])),pid))
            selected[task][slug]=best;summary[task][slug]=ss
        for embedding in (('jina-v2','jina-v2-md') if task=='skills' else ('jina-v2',)):
            for kind in ('lr','mlp'):
                slug=embedding+'-'+kind;path=f'learned/{slug}/{task}/selection.json';s=read(state/path)
                selected[task][slug]=s['selected'];summary[task][slug]=s.get('aggregate') or s['validation'];files[path]=digest(state/path)
                for rel,h in s['evidence'].items():
                    if digest(state/rel)!=h:raise ValueError('Changed learned evidence')
                    files[rel]=h
    write(state/'validation-summary.json',summary);files['validation-summary.json']=digest(state/'validation-summary.json')
    write(state/'freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),selected=selected,files=files));print(canonical(selected))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','freeze']);p.add_argument('--state',required=True);a=p.parse_args();globals()[a.action](a.state)
