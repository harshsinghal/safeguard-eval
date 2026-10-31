"""Fill missing native decision scores with unchanged, pinned policy packs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import time
import threading
import urllib.error
from .common import *


def cases(state,ds,split):
 rr=rows(state/f'inputs/{ds}/{split}.jsonl')
 if any(set(r)!={'id','prompt','prompt_sha256'} for r in rr):raise ValueError('Labels or metadata in model input')
 return rr

def check_canary(state,ds,model,rr):
 old={r['id']:r for r in rows(state/f'canary-reference/{ds}/{model}.jsonl.gz')}
 if len(rr)!=16 or set(old)!={r['id'] for r in rr}:raise ValueError('Canary population mismatch')
 delta=max(abs(r['score']-old[r['id']]['score']) for r in rr)
 flips=sum(r['prediction']!=old[r['id']]['prediction'] for r in rr)
 result=dict(n=len(rr),max_score_difference=delta,native_decision_changes=flips,tolerance=.02)
 write(state/f'new-runs/{model}/{ds}/canary-check.json',result)
 if delta>.02 or flips:raise ValueError('New scoring differs from archive; stop before bulk inference: '+str(result))
 return result

def native(state,model,vendor):
 from evals.decision_models.adapters import Adapter
 state=Path(state);verify(state);engine=Adapter(model,vendor)
 for ds in POOL:
  policy=read(state/f'policies/{ds}/{model}.json')
  for split in ['canary','fit','validation']:
   dest=state/f'new-runs/{model}/{ds}/{split}.jsonl'
   todo=cases(state,ds,split);existing=rows(dest) if dest.exists() else []
   byid={r['id']:r for r in todo};seen={r['id'] for r in existing}
   if len(seen)!=len(existing) or not seen<=set(byid):raise ValueError('Bad resume output')
   for r in existing:
    if r['prompt_sha256']!=byid[r['id']]['prompt_sha256'] or r['policy_sha256']!=digest(state/f'policies/{ds}/{model}.json'):raise ValueError('Changed resume policy/content')
   encoded=[]
   for r in todo:
    if r['id'] not in seen:encoded.append((r,engine.encode(r['prompt'],policy)))
   encoded.sort(key=lambda t:(t[1][2],t[0]['id']))
   dest.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic();done=len(existing)
   def forward(part):
    try:return engine.forward([e for _,e in part])
    except engine.torch.OutOfMemoryError:
     engine.torch.cuda.empty_cache()
     if len(part)==1:raise
     k=len(part)//2;return forward(part[:k])+forward(part[k:])
   with dest.open('a') as f:
    i=0
    while i<len(encoded):
     j=i+1
     while j<len(encoded) and j-i<16 and encoded[j][1][2]*(j-i+1)<=8192:j+=1
     part=encoded[i:j];out=forward(part)
     for (r,e),score in zip(part,out):
      item=dict(id=r['id'],prompt_sha256=r['prompt_sha256'],**score,policy_sha256=digest(state/f'policies/{ds}/{model}.json'),input_tokens=e[2],model=model)
      f.write(json.dumps(item,allow_nan=False)+'\n');f.flush()
     done+=len(part);i=j
     if done%256<len(part) or done==len(todo):print(json.dumps(dict(model=model,dataset=ds,split=split,done=done,total=len(todo),seconds=round(time.monotonic()-start,1))),flush=True)
   rr=rows(dest)
   if len(rr)!=len(todo):raise ValueError('Incomplete native scores')
   if split=='canary':check_canary(state,ds,model,rr)
   meta=rows(state/f'metadata/{ds}/{split}.jsonl.gz')
   write_rows(state/f'scores/{ds}/{model}/{split}.jsonl.gz',align_scores(meta,rr))
   write(dest.with_suffix('.manifest.json'),dict(created_utc=now(),model=model,split=split,dataset=ds,n=len(rr),sha256=digest(dest),gpu=engine.torch.cuda.get_device_name(),torch=engine.torch.__version__,seconds=time.monotonic()-start,registration_sha256=digest(state/'registration.json')))
 print('NATIVE_COMPLETE',model,flush=True)

def jev(state,keyfile):
 from evals.jev.api import Ledger,read_key,payload,post,parse,billed_cost,hash_value,RESERVE,save
 state=Path(state);verify(state);ledger=Ledger(state/'billing.sqlite',0.,cap=1.0);ledger.assert_no_pending();key=read_key(keyfile)
 abort=threading.Event()
 for ds in POOL:
  policies=read(state/f'policies/{ds}/jev-pack.json')
  for split in ['canary','fit','validation']:
   rr=cases(state,ds,split);raw=state/f'private-responses/{ds}/{split}';raw.mkdir(parents=True,exist_ok=True)
   def one(r):
    if abort.is_set():raise RuntimeError('Stopped after provider error')
    body=payload(r['prompt'],policies);h=hash_value(body);uid=hash_value([ds,split,r['id'],h]);cache=raw/(uid+'.json')
    if cache.exists():record=read(cache);response=record['response']
    else:
     ledger.reserve(uid);start=time.monotonic()
     try:response=post(body,key)
     except urllib.error.HTTPError as e:
      ledger.settle(uid,RESERVE,'error_upper_bound');abort.set();save(raw/(uid+'.error.json'),dict(http_status=e.code,request_sha256=h));raise RuntimeError('Jev HTTP '+str(e.code)) from None
     except Exception as e:
      abort.set();save(raw/(uid+'.error.json'),dict(error_type=type(e).__name__,request_sha256=h));raise RuntimeError('Jev transport failed; reservation retained') from None
     record=dict(id=r['id'],request_sha256=h,response=response,latency_seconds=time.monotonic()-start);save(cache,record)
     try:ledger.settle(uid,billed_cost(response))
     except Exception:abort.set();raise
    try:out=parse(response,policies)['detailed']
    except Exception:abort.set();raise
    return dict(id=r['id'],prompt_sha256=r['prompt_sha256'],**out,model=response['model'],provider=response['provider'],request_sha256=h,response_id=response['id'])
   results=[]
   with ThreadPoolExecutor(max_workers=8) as pool:
    futures=[pool.submit(one,r) for r in rr]
    for future in as_completed(futures):
     results.append(future.result())
     if len(results)%256==0 or len(results)==len(rr):print(ds,split,len(results),'/',len(rr),'accounted_usd',ledger.totals()['total_accounted_usd'],flush=True)
   write_rows(state/f'new-runs/jev/{ds}/{split}.jsonl',results)
   if split=='canary':check_canary(state,ds,'jev',results)
   meta=rows(state/f'metadata/{ds}/{split}.jsonl.gz');write_rows(state/f'scores/{ds}/jev/{split}.jsonl.gz',align_scores(meta,results))
   write(state/'api-billing.json',ledger.totals())
 ledger.assert_no_pending();write(state/'api-billing.json',ledger.totals());print('JEV_COMPLETE',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--model',choices=['kev','clef','jev'],required=True);p.add_argument('--vendor');p.add_argument('--keyfile');a=p.parse_args()
 if a.model=='jev':jev(a.state,a.keyfile)
 else:native(a.state,a.model,a.vendor)
