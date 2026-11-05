"""Resumable inference with native model adapters and strict split gates."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
import math
import time
import urllib.request
import urllib.error
from .common import *
from .requests import safeguard_payload,jev_payload

def jobs(state,model,task,split):
    catalog=read(Path(state)/f'policies/{task}/{model}.json')
    if split=='test':
        chosen=read(Path(state)/'selection.json')['models'][model][task]['selected']
        catalog={p:catalog[p] for p in dict.fromkeys(('initial',chosen))} if chosen is not None else {}
    rr=data(state,task,'fit' if split=='smoke' else split,model)
    if split=='smoke':rr=sorted(rr,key=lambda r:r['id'])[:12];catalog={'initial':catalog['initial']}
    for pid,p in catalog.items():
        jj=[]
        for r in rr:
            body={'content':r['prompt'],'policy':p}
            jj.append(dict(metadata(r),policy_id=pid,body=body,request_sha256=hash_value(body)))
        yield pid,jj

def pending(path,jj):
    old=rows(path) if path.exists() else [];cached={r['id']:r for r in old};expected={j['id']:j for j in jj}
    if len(cached)!=len(old) or not set(cached)<=set(expected):raise ValueError('Bad prediction cache population')
    for rid,r in cached.items():
        if any(r[k]!=expected[rid][k] for k in ('request_sha256','expected','prompt_sha256','group','split','policy_id')):
            raise ValueError('Cache request mismatch')
    return [j for j in jj if j['id'] not in cached]

def record(j,result,model):
    if result['prediction'] not in ('ALLOW','BLOCK','ERROR'):raise ValueError('Invalid decision')
    score=result.get('score')
    if score is not None and (not math.isfinite(score) or not 0<=score<=1):raise ValueError('Invalid score')
    return dict({k:v for k,v in j.items() if k!='body'},**result,model=model)

class Remote:
    def __init__(self,state,model,keyfile):
        self.state=Path(state);self.model=model
        if model=='jev':
            from evals.jev.api import Ledger,read_key
            self.ledger=Ledger(self.state/'jev-billing.sqlite',cap=2.0);self.ledger.assert_no_pending();self.key=read_key(keyfile)
        else:
            with urllib.request.urlopen('http://127.0.0.1:8000/v1/models',timeout=20) as r:x=json.load(r)
            if MODELS[model]['model'] not in [m['id'] for m in x['data']]:raise ValueError('Wrong local served model')

    def one(self,j,task,split,pid):
        from evals.jev.api import post,billed_cost,parse,RESERVE
        uid=hash_value([self.model,task,split,j['id'],j['request_sha256']])
        body=(jev_payload if self.model=='jev' else safeguard_payload)(**j['body'])
        final=self.state/f'private-responses/{self.model}/{uid}.json'
        if final.exists():
            cached=read(final)
            if cached['request_sha256']!=hash_value(body):raise ValueError('Response cache mismatch')
            return cached['result']
        for attempt in range(3):
            aid=f'{uid}-{attempt}';start=time.monotonic()
            if self.model=='jev':self.ledger.reserve(aid)
            try:
                if self.model=='jev':x=post(body,self.key)
                else:
                    req=urllib.request.Request('http://127.0.0.1:8000/v1/chat/completions',data=canonical(body).encode(),headers={'Content-Type':'application/json'})
                    with urllib.request.urlopen(req,timeout=600) as r:x=json.load(r)
            except (urllib.error.URLError,TimeoutError,ConnectionError) as exc:
                # Failed request cost is unknown: retain a full reservation as an upper bound.
                if self.model=='jev':self.ledger.settle(aid,RESERVE,'transport_error_upper_bound')
                write(self.state/f'private-errors/{self.model}/{aid}.json',dict(error_type=type(exc).__name__,http_status=getattr(exc,'code',None)))
                if attempt<2 and (not isinstance(exc,urllib.error.HTTPError) or exc.code in (429,500,502,503,504)):
                    time.sleep(2**attempt);continue
                return dict(prediction='ERROR',score=None,error_type=type(exc).__name__,transport_error=True,attempts=attempt+1)
            # Preserve provider evidence before interpreting or settling it.
            write(self.state/f'private-responses/{self.model}/{aid}.raw.json',dict(request_sha256=hash_value(body),response=x))
            if self.model=='jev':self.ledger.settle(aid,billed_cost(x))
            try:
                if self.model=='jev':result=parse(x,['moderation'])['moderation']
                else:
                    c=x['choices'][0]
                    if x['model']!=MODELS[self.model]['model'] or c['finish_reason']!='stop':raise ValueError('Wrong model or truncated completion')
                    a=json.loads(c['message']['content'])
                    if set(a)!={'decision'} or a['decision'] not in ('ALLOW','BLOCK'):raise ValueError('Malformed binary JSON')
                    result=dict(prediction=a['decision'],score=None)
                result.update(usage=x.get('usage'),response_model=x.get('model'),response_provider=x.get('provider','self-hosted vLLM'),seconds=time.monotonic()-start)
            except (KeyError,ValueError,IndexError,TypeError) as exc:
                result=dict(prediction='ERROR',score=None,error_type=type(exc).__name__,usage=x.get('usage'))
            write(final,dict(request_sha256=hash_value(body),result=result))
            return result

def run(state,model,split,vendor=None,keyfile=None,concurrency=8):
    state=Path(state);verify(state,test=split=='test')
    if not read(state/'authorization.json')['approved']:raise ValueError('Missing authorization')
    if model=='jev' and not keyfile:raise ValueError('Need a key-file path, never a literal key')
    native=model not in ('jev','safeguard');engine=None;start=time.monotonic();errors=0;infrastructure_errors=0
    lengths={(r['id'],r['model']):r['candidates'] for r in rows(state/'input-lengths.jsonl')}
    for task in TASKS:
        for pid,jj in jobs(state,model,task,split):
            path=state/f'predictions/{model}/{task}/{split}/{pid}.jsonl';todo=pending(path,jj)
            path.parent.mkdir(parents=True,exist_ok=True)
            if not todo:
                if not path.exists():path.touch()
                continue
            if engine is None:
                if native:
                    from evals.prompt_injection.infer import Native
                    engine=Native(model,vendor)
                else:engine=Remote(state,model,keyfile)
            def one(j):
                if not native:return engine.one(j,task,split,pid)
                try:
                    enc=engine.encode(j)
                    measured=enc[2] if model in ('kev','clef') else len(enc) if model=='shieldstral' else None
                    if measured is not None and measured!=lengths[j['id'],model][pid]['tokens']:
                        raise ValueError('Runtime tokenization differs from preflight')
                    result=engine.forward([enc])[0]
                    if model=='policylm' and (result['windows']!=1 or result['variants']!=1):
                        raise ValueError('Native preprocessing violated complete-input eligibility')
                    result['input_tokens']=measured
                    return result
                except (ValueError,RuntimeError) as exc:
                    write(state/f'private-errors/{model}/{task}-{split}-{pid}-{j["id"]}.json',dict(error_type=type(exc).__name__,error=str(exc)))
                    return dict(prediction='ERROR',score=None,error_type=type(exc).__name__,transport_error=True)
            finished=len(jj)-len(todo)
            def save_result(j,r,f):
                nonlocal finished,errors,infrastructure_errors
                f.write(canonical(record(j,r,model))+'\n');f.flush();finished+=1
                errors+=r['prediction']=='ERROR';infrastructure_errors+=bool(r.get('transport_error'))
                if finished%64==0 or finished==len(jj):
                    print(canonical(dict(model=model,task=task,split=split,policy=pid,done=finished,total=len(jj),errors=errors)),flush=True)
                if infrastructure_errors>=3:raise RuntimeError('Repeated infrastructure failures; stop and preserve evidence')
            with path.open('a') as f:
                if native:
                    for j in todo:save_result(j,one(j),f)
                else:
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        it=iter(todo);active={}
                        def submit():
                            j=next(it,None)
                            if j is not None:active[pool.submit(one,j)]=j
                        for _ in range(concurrency):submit()
                        while active:
                            done,_=wait(active,return_when=FIRST_COMPLETED)
                            for future in done:
                                j=active.pop(future);save_result(j,future.result(),f);submit()
    runtime=dict(created_utc=now(),seconds=time.monotonic()-start,model=MODELS[model],errors=errors,
        concurrency=1 if native else concurrency)
    if native and engine is not None:
        runtime.update(torch=engine.torch.__version__,gpu=engine.torch.cuda.get_device_name(),dtype='bfloat16')
    if model=='jev' and engine is not None:write(state/'jev-costs.json',engine.ledger.totals())
    write(state/f'runtime/{model}-{split}.json',runtime)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--model',choices=MODEL_NAMES,required=True)
    p.add_argument('--split',choices=['smoke','validation','test'],required=True);p.add_argument('--vendor');p.add_argument('--keyfile');p.add_argument('--concurrency',type=int,default=8)
    run(**vars(p.parse_args()))
