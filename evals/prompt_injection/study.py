"""Registration, fitting-derived examples, validation selection, sealed test jobs."""
import argparse
from .common import *
from .policies import initial,render,with_examples

def register(state):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    write(state/'policies/initial.json',initial())
    files={str(p.relative_to(state)):digest(p) for p in [state/'source-manifest.json',state/'data-audit.json',
        state/'policies/initial.json',*sorted((state/'data').glob('*.jsonl')),*sorted((state/'metadata').glob('*.jsonl'))]}
    write(state/'registration.json',dict(created_utc=now(),models=MODELS,files=files,sources=sources(),
        selection='equal-source mean balanced accuracy on validation; tie: mean macro F1, shorter serialized policy, policy id',
        fit_example_rule='two per label; brief-policy errors first; <=280 characters; distinct groups; stable hash order; fallback to correctly classified fitting rows',
        calibration=False,ensemble=False,test_data_shown_to_policy_author=False))
    print('Registered protocol, data and initial policies; no model requests sent.')

def author(state):
    state=Path(state);verify(state)
    fit={r['id']:r for r in rows(state/'data/fit.jsonl')}
    for slug in MODELS:
        dest=state/'policies'/slug/'candidates.json'
        if dest.exists():raise ValueError('Already authored: '+slug)
        pred=completed(state,slug,'fit','brief');examples=[];used=set()
        for label in ('BLOCK','ALLOW'):
            pool=[r for r in pred if r['expected']==label and len(fit[r['id']]['prompt'])<=280 and r['prediction']!='ERROR']
            pool.sort(key=lambda r:(r['prediction']==r['expected'],hash_value(r['id'])))
            for r in pool:
                if r['group'] in used:continue
                used.add(r['group']);examples.append(fit[r['id']])
                if sum(x['expected']==label for x in examples)==2:break
        if len(examples)!=4:raise ValueError('Insufficient fitting examples; amend before proceeding')
        pp=initial();pp['examples']=with_examples(examples)
        write(dest,{pid:render(p,slug) for pid,p in pp.items()})
        write(dest.parent/'example-provenance.json',[
            {**{k:v for k,v in r.items() if k!='prompt'},'brief_prediction':next(x['prediction'] for x in pred if x['id']==r['id'])} for r in examples])
    write(state/'policy-freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),
        files={str(p.relative_to(state)):digest(p) for p in sorted((state/'policies').rglob('*.json'))},
        fitting={slug:digest(state/f'predictions/{slug}/fit/brief.jsonl') for slug in MODELS}))
    print('All model-specific example policies frozen using fitting data only.')

def check_policies(state):
    state=Path(state);f=read(state/'policy-freeze.json')
    if f['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Changed registration')
    for p,h in f['files'].items():
        if digest(state/p)!=h:raise ValueError('Frozen policy changed')
    for slug,h in f['fitting'].items():
        if digest(state/f'predictions/{slug}/fit/brief.jsonl')!=h:raise ValueError('Fitting evidence changed')

def jobs(state,split):
    state=Path(state);verify(state,test=split=='test')
    if split!='fit':check_policies(state)
    data=rows(state/f'data/{split}.jsonl');catalog={}
    for slug in MODELS:
        pp={'brief':render(initial()['brief'],slug)} if split=='fit' else read(state/f'policies/{slug}/candidates.json')
        if split=='test':
            selected=read(state/'freeze.json')['selected'][slug]
            pp={p:pp[p] for p in dict.fromkeys(['brief',selected])}
        catalog[slug]={}
        for pid,p in pp.items():
            dest=state/f'jobs/{slug}/{split}/{pid}.jsonl'
            if dest.exists():raise ValueError('Jobs already exist')
            rr=[]
            for r in data:
                body={'content':r['prompt'],'policy':p}
                rr.append({**{k:v for k,v in r.items() if k!='prompt'},'policy_id':pid,'body':body,
                    'request_sha256':hash_value(body),'policy_sha256':hash_value(p)})
            jsonl(dest,rr);catalog[slug][pid]=digest(dest)
    write(state/f'jobs/{split}-manifest.json',catalog)
    print(canonical({s:{p:len(data) for p in ps} for s,ps in catalog.items()}))

def freeze(state):
    state=Path(state);verify(state);check_policies(state)
    if (state/'freeze.json').exists():raise ValueError('Already selected')
    selected={};summary={};files={'policy-freeze.json':digest(state/'policy-freeze.json')}
    files.update(read(state/'policy-freeze.json')['files'])
    for slug in MODELS:
        candidates=read(state/f'policies/{slug}/candidates.json');summary[slug]={}
        for pid,p in candidates.items():
            rr=completed(state,slug,'validation',pid)
            by={ds:measures([r for r in rr if r['dataset']==ds]) for ds in ('deepset','safeguard')}
            summary[slug][pid]=dict(by_source=by,balanced_accuracy=sum(m['balanced_accuracy'] for m in by.values())/2,
                macro_f1=sum(m['macro_f1'] for m in by.values())/2,policy_bytes=len(canonical(p).encode()))
            path=f'predictions/{slug}/validation/{pid}.jsonl';files[path]=digest(state/path)
        selected[slug]=min(candidates,key=lambda p:(-summary[slug][p]['balanced_accuracy'],
            -summary[slug][p]['macro_f1'],summary[slug][p]['policy_bytes'],p))
    write(state/'validation-summary.json',summary);files['validation-summary.json']=digest(state/'validation-summary.json')
    write(state/'freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),
        selected=selected,files=files,no_threshold_search=True))
    print(canonical({'selected':selected}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['register','author','jobs','freeze']);p.add_argument('--state',required=True)
    p.add_argument('--split',choices=['fit','validation','test']);a=p.parse_args()
    if a.command=='jobs':jobs(a.state,a.split)
    else:globals()[a.command](a.state)
