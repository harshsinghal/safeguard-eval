import argparse
from collections import Counter
import hashlib
from pathlib import Path
import shutil
from .common import *

def prepare(state,prior):
    state,prior=Path(state),Path(prior)
    if state.exists():raise ValueError('Use a new state directory')
    populations=[];hashes={};counts={}
    old=read(prior/'registration.json')
    for split in ('fit','validation','test'):
        data=rows(prior/f'inputs/wildguard/{split}.jsonl')
        meta=rows(prior/f'metadata/wildguard/{split}.jsonl.gz')
        for rel in (f'inputs/wildguard/{split}.jsonl',f'metadata/wildguard/{split}.jsonl.gz'):
            if digest(prior/rel)!=old['data_hashes'][rel]:raise ValueError('Prior data changed')
        if [r['id'] for r in data]!=[r['id'] for r in meta]:raise ValueError('Misaligned inputs')
        for x,m in zip(data,meta):
            if set(x)!={'id','prompt','prompt_sha256'} or hashlib.sha256(x['prompt'].encode()).hexdigest()!=m['prompt_sha256']:
                raise ValueError('Invalid input record')
        populations.append(meta)
        for rel,rr in ((f'inputs/{split}.jsonl',data),(f'metadata/{split}.jsonl.gz',meta)):
            write_rows(state/rel,rr);hashes[rel]=digest(state/rel)
        counts[split]={'n':len(meta),'labels':dict(Counter(r['expected'] for r in meta))}
    assert_disjoint(*populations)
    if [counts[s]['n'] for s in ('fit','validation','test')]!=[4096,1536,1699]:raise ValueError('Wrong populations')
    fit=[dict(x,**{k:v for k,v in m.items() if k not in x}) for x,m in zip(rows(state/'inputs/fit.jsonl'),populations[0])]
    bank,excluded=bank_from_fit(fit);fixed=fixed_ids(bank)
    write_rows(state/'private-bank.jsonl',bank)
    write_rows(state/'bank-metadata.jsonl.gz',[{k:v for k,v in r.items() if k!='prompt'} for r in bank])
    fixed_groups={r['group'] for r in bank if r['id'] in fixed}
    smoke=[r for r in fit if r['group'] not in fixed_groups and r['prompt'].strip()][:32]
    write_rows(state/'inputs/smoke.jsonl',[{k:r[k] for k in ('id','prompt','prompt_sha256')} for r in smoke])
    write_rows(state/'metadata/smoke.jsonl.gz',[{k:v for k,v in r.items() if k!='prompt'} for r in smoke])
    from evals.jev.study import base_policies
    for model in MODELS:
        p=base_policies('wildguard')['brief'] if model in ('jev','kev') else read(ROOT/f'evals/wildguard/policies/p4-{model}.json')
        write(state/f'policies/{model}.json',p)
        hashes[f'policies/{model}.json']=digest(state/f'policies/{model}.json')
    for rel in ('private-bank.jsonl','bank-metadata.jsonl.gz','inputs/smoke.jsonl','metadata/smoke.jsonl.gz'):
        hashes[rel]=digest(state/rel)
    write(state/'registration.json',{'created_utc':now(),'sources':sources(),'hashes':hashes,
        'models':MODELS,'encoder':ENCODER,'populations':counts,'bank_n':len(bank),
        'bank_labels':dict(Counter(r['expected'] for r in bank)),'bank_exclusions':excluded,'fixed_ids':fixed,
        'decisions':'native argmax for Choice; >=0.5 for PolicyLM and Shieldstral; no calibration',
        'primary_metric':'accuracy','prior_registration_sha256':digest(prior/'registration.json')},exclusive=True)
    print(canonical({'populations':counts,'bank_n':len(bank),'excluded':excluded}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--prior',required=True)
    prepare(**vars(p.parse_args()))
