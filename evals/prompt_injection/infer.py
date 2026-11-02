"""Native frozen-weight inference. Test jobs require every model's selection freeze."""
import argparse
import math
import time
from .common import *
from .study import check_policies

def load_jobs(state,slug,split,pid):
    state=Path(state);verify(state,test=split=='test')
    if split!='fit':check_policies(state)
    p=state/f'jobs/{slug}/{split}/{pid}.jsonl'
    if digest(p)!=read(state/f'jobs/{split}-manifest.json')[slug][pid]:raise ValueError('Jobs changed')
    jj=rows(p)
    for j in jj:
        if hash_value(j['body'])!=j['request_sha256']:raise ValueError('Changed input')
    return jj

def pending(state,slug,split,pid,jobs):
    p=Path(state)/f'predictions/{slug}/{split}/{pid}.jsonl'
    old=rows(p) if p.exists() else [];done={r['id']:r for r in old}
    if len(done)!=len(old) or not set(done)<={j['id'] for j in jobs}:raise ValueError('Invalid cached population')
    for j in jobs:
        if j['id'] in done and done[j['id']]['request_sha256']!=j['request_sha256']:raise ValueError('Cache input mismatch')
    return p,[j for j in jobs if j['id'] not in done]

def record(job,result,slug):
    if result['prediction'] not in ('ALLOW','BLOCK','ERROR'):raise ValueError('Invalid classification')
    if result.get('score') is not None and (not math.isfinite(result['score']) or not 0<=result['score']<=1):raise ValueError('Invalid score')
    return {**{k:v for k,v in job.items() if k!='body'},**result,'model':slug}

class Native:
    def __init__(self,slug,vendor):
        self.slug=slug
        if slug in ('kev','clef'):
            from evals.decision_models.adapters import Adapter
            # Use serial decision heads: earlier studies observed batch variation.
            self.engine=Adapter(slug,vendor,serving_fused=slug=='kev')
            self.torch=self.engine.torch
        else:
            from evals.retrieved_examples.native import Engine
            self.engine=Engine(slug,vendor);self.torch=self.engine.torch
    def encode(self,j):
        if self.slug in ('kev','clef'):return self.engine.encode(j['body']['content'],j['body']['policy'])
        return self.engine.encode(j)
    def forward(self,enc):
        if self.slug!='policylm':return self.engine.forward(enc)
        out=[]
        with self.torch.inference_mode():
            for text,p,name in enc:
                r=self.engine.native.classify(text,p,cutoff='precision',clean=True)
                score=float(r.categories[name].score)
                if abs(float(r.cutoff)-.335)>1e-9:raise ValueError('Publisher preset changed')
                out.append(dict(score=score,prediction='BLOCK' if score>=.335 else 'ALLOW',
                    windows=r.windows,variants=r.variants,cleaned=r.cleaned,cutoff=.335))
        return out

def run(state,slug,split,vendor):
    state=Path(state);verify(state,test=split=='test')
    authorization=read(state/'authorization.json')
    if not authorization.get('approved') or authorization['experiment_cap_usd']>8:raise ValueError('Budget not approved')
    catalog=read(state/f'jobs/{split}-manifest.json')[slug]
    engine=Native(slug,vendor);start=time.monotonic();errors=0
    for pid in catalog:
        jj=load_jobs(state,slug,split,pid);out,todo=pending(state,slug,split,pid,jj)
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('a') as f:
            for i,j in enumerate(todo):
                try:
                    result=engine.forward([engine.encode(j)])[0]
                except (ValueError,RuntimeError) as exc:
                    # Operational failures remain in denominators. Do not label
                    # the attack successful/blocked on behalf of a failed model.
                    result=dict(prediction='ERROR',score=None,error_type=type(exc).__name__)
                    errors+=1
                    write(state/f'private-errors/{slug}/{split}/{pid}-{hash_value(j["id"])[:16]}.json',
                        {'id':j['id'],'error':str(exc)})
                f.write(canonical(record(j,result,slug))+'\n');f.flush()
                if errors>=5:raise RuntimeError('Repeated inference failures; stop and inspect before continuing')
                if i%64==0 or i==len(todo)-1:
                    print(canonical(dict(model=slug,split=split,policy=pid,completed=len(jj)-len(todo)+i+1,total=len(jj),errors=errors)),flush=True)
    write(state/f'runtime/{slug}-{split}.json',dict(created_utc=now(),gpu=engine.torch.cuda.get_device_name(),
        torch=engine.torch.__version__,batch_size=1,seconds=time.monotonic()-start,
        dtype='bfloat16',serial=True,errors=errors))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--slug',choices=['policylm','shieldstral','kev','clef'],required=True)
    p.add_argument('--split',choices=['fit','validation','test'],required=True);p.add_argument('--vendor',required=True)
    run(**vars(p.parse_args()))
