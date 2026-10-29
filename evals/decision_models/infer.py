"""Durable native-head inference. Development and test are separate invocations."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time

from evals.ensemble.common import digest, now, read, rows
from evals.jev.api import hash_value, save
from evals.jev.study import DATA, read_data
from evals.decision_models.study import (MODELS, author, pred_path, sources, verify,
    verify_freeze, verify_policies)
from evals.decision_models.adapters import Adapter


def checked_resume(path, expected, policy_hash):
    rr=rows(path) if path.exists() else []
    seen=set(); byid={r['id']:r for r in expected}
    for r in rr:
        if r['id'] in seen or r['id'] not in byid or r['policy_sha256']!=policy_hash:
            raise ValueError('Changed or duplicated resume input')
        if r['prompt_sha256']!=byid[r['id']]['prompt_sha256']:
            raise ValueError('Changed resume content')
        seen.add(r['id'])
    return seen


def predict(state, slug, ds, split, pid, policy, adapter, batch_tokens, max_batch):
    rr=read_data(state,ds,split); path=pred_path(state,slug,ds,split,pid)
    path.parent.mkdir(parents=True,exist_ok=True)
    ph=hash_value(policy); seen=checked_resume(path,rr,ph)
    pending=[]; rejected=[]
    for r in rr:
        if r['id'] in seen: continue
        try: pending.append((r,adapter.encode(r['prompt'],policy)))
        except ValueError as exc: rejected.append((r,dict(prediction='ERROR',score=None,error=str(exc))))
    pending.sort(key=lambda x:(x[1][2],x[0]['id']))
    start=time.monotonic(); completed=len(seen)
    def append(handle,r,out,n=0):
        nonlocal completed
        metadata={k:v for k,v in r.items() if k!='prompt'}
        metadata.update(out,model=slug,policy=pid,policy_sha256=ph,input_tokens=n,created_utc=now())
        handle.write(json.dumps(metadata,ensure_ascii=False,allow_nan=False)+'\n'); handle.flush()
        completed+=1
    def forward(part):
        try:
            return adapter.forward([p[1] for p in part])
        except adapter.torch.OutOfMemoryError:
            adapter.torch.cuda.empty_cache()
            if len(part)==1: return [dict(prediction='ERROR',score=None,error='CUDA out of memory; full input retained')]
            mid=len(part)//2
            return forward(part[:mid])+forward(part[mid:])
    with path.open('a') as handle:
        for r,out in rejected: append(handle,r,out)
        i=0
        while i<len(pending):
            j=i+1
            while j<len(pending) and j-i<max_batch and pending[j][1][2]*(j-i+1)<=batch_tokens: j+=1
            part=pending[i:j]; t=time.monotonic(); outputs=forward(part)
            seconds=time.monotonic()-t
            for (r,enc),out in zip(part,outputs):
                append(handle,r,dict(out,batch_size=len(part),batch_seconds=seconds),enc[2])
            i=j
            if completed%100<len(part) or i==len(pending):
                print(json.dumps(dict(model=slug,dataset=ds,split=split,policy=pid,completed=completed,total=len(rr),
                    elapsed_seconds=round(time.monotonic()-start,1))),flush=True)
    if completed!=len(rr): raise ValueError('Incomplete run')
    save(path.with_suffix('.manifest.json'),dict(model=MODELS[slug],policy=pid,policy_sha256=ph,
        split=split,dataset=ds,rows=completed,predictions_sha256=digest(path),sources=sources(),created_utc=now()))


def parity(state,slug,adapter):
    # Fit-only smoke checks cover short and long records across both tasks.
    encs=[]
    for ds in DATA:
        rr=read_data(state,ds,'fit'); pp=read(Path(state)/'policies'/ds/'initial.json')
        sample=sorted(rr,key=lambda r:len(r['prompt']))
        for r in (sample[0],sample[len(sample)//2],sample[-1]):
            encs.append(adapter.encode(r['prompt'],pp['brief']))
    single=[adapter.forward([e])[0] for e in encs]
    # Keep the smoke batch within the same memory budget as normal inference.
    batched=[]
    for i in range(0,len(encs),2): batched+=adapter.forward(encs[i:i+2])
    delta=max(abs(a['score']-b['score']) for a,b in zip(single,batched))
    flips=sum(a['prediction']!=b['prediction'] for a,b in zip(single,batched))
    result=dict(created_utc=now(),max_probability_difference=delta,argmax_changes=flips,n=len(encs),
        single=single,batched=batched)
    save(Path(state)/slug/'parity.json',result)
    if delta>.02 or flips: raise ValueError('Batch parity failed; investigate before bulk inference')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--state',required=True); ap.add_argument('--vendor',required=True)
    ap.add_argument('--model',choices=MODELS,required=True); ap.add_argument('--stage',choices=['development','test'],required=True)
    ap.add_argument('--batch-tokens',type=int,default=8192); ap.add_argument('--max-batch',type=int,default=16)
    a=ap.parse_args(); state=Path(a.state); verify(state)
    if a.stage=='test': verify_freeze(state)
    adapter=Adapter(a.model,a.vendor)
    packages={}
    for name in ('torch','transformers','peft','numpy','safetensors','huggingface_hub','flash-linear-attention','causal-conv1d'):
        try: packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: pass
    save(state/a.model/(a.stage+'-environment.json'),dict(created_utc=now(),packages=packages,
        device=adapter.torch.cuda.get_device_name(),model=MODELS[a.model],temperature=adapter.temperature,
        batch_tokens=a.batch_tokens,max_batch=a.max_batch,sources=sources()))
    if a.stage=='development':
        if not (state/a.model/'parity.json').exists(): parity(state,a.model,adapter)
        for ds in DATA:
            pp=read(state/'policies'/ds/'initial.json')
            for pid in ('brief','detailed'): predict(state,a.model,ds,'fit',pid,pp[pid],adapter,a.batch_tokens,a.max_batch)
        if not (state/a.model/'policies-freeze.json').exists(): author(state,a.model)
        verify_policies(state,a.model)
        split='validation'
    else: split='test'
    for ds in DATA:
        pp=read(state/'policies'/a.model/ds/'final.json')
        for pid in ('brief','detailed','examples'): predict(state,a.model,ds,split,pid,pp[pid],adapter,a.batch_tokens,a.max_batch)
    print(a.model.upper()+'_'+a.stage.upper()+'_COMPLETE',flush=True)

if __name__=='__main__': main()
