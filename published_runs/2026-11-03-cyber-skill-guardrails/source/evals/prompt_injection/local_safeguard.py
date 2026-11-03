"""Self-hosted Safeguard fallback after provider rate limits, before validation.

Only loopback is supported. The request's policy/content/decoding match the API
preflight; provider routing is removed and reasoning_effort uses vLLM's field.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import time
import urllib.error
import urllib.request
from .common import *
from .api import payload
from .infer import load_jobs,pending,record

def run(state,split,concurrency=4):
    state=Path(state);verify(state,test=split=='test')
    if not read(state/'authorization.json').get('approved'):raise ValueError('No authorization')
    base='http://127.0.0.1:8000/v1'
    with urllib.request.urlopen(base+'/models',timeout=20) as r:model_info=json.load(r)
    if MODELS['safeguard']['model'] not in [m['id'] for m in model_info['data']]:raise ValueError('Wrong local model')
    start=time.monotonic();errors=0;transport_errors=0
    def one(j,pid):
        body=payload(j,'safeguard');body.pop('provider');body.pop('reasoning');body['reasoning_effort']='medium';body['max_tokens']=8192
        req=urllib.request.Request(base+'/chat/completions',data=canonical(body).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=600) as r:x=json.load(r)
            uid=hash_value({'request':j['request_sha256'],'id':j['id'],'split':split,'policy':pid})
            write(state/f'private-local-safeguard/{uid}.json',x)
            c=x['choices'][0]
            if x['model']!=MODELS['safeguard']['model'] or c['finish_reason']!='stop':raise ValueError('Invalid/truncated completion')
            answer=json.loads(c['message']['content'])
            if set(answer)!={'decision'} or answer['decision'] not in ('ALLOW','BLOCK'):raise ValueError('Invalid binary JSON')
            result={'prediction':answer['decision'],'score':None,'usage':x.get('usage'),
                'response_model':x['model'],'response_provider':'self-hosted vLLM','attempt_id':uid}
        except (ValueError,KeyError,IndexError,TimeoutError,ConnectionError,urllib.error.URLError) as exc:
            result={'prediction':'ERROR','score':None,'error_type':type(exc).__name__,
                'transport_error':isinstance(exc,(TimeoutError,ConnectionError,urllib.error.URLError))}
            write(state/f'private-errors/safeguard/{split}/{pid}-{hash_value(j["id"])[:16]}.json',{'id':j['id'],'error':str(exc)})
        return record(j,result,'safeguard')
    for pid in read(state/f'jobs/{split}-manifest.json')['safeguard']:
        jj=load_jobs(state,'safeguard',split,pid);out,todo=pending(state,'safeguard',split,pid,jj)
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('a') as f, ThreadPoolExecutor(max_workers=concurrency) as pool:
            iterator=iter(todo);active={};done_count=len(jj)-len(todo)
            def submit_next():
                j=next(iterator,None)
                if j is not None:active[pool.submit(one,j,pid)]=j['id']
            for _ in range(concurrency):submit_next()
            while active:
                finished,_=wait(active,return_when=FIRST_COMPLETED)
                for future in finished:
                    active.pop(future);r=future.result();f.write(canonical(r)+'\n');f.flush()
                    errors+=r['prediction']=='ERROR';transport_errors+=r.get('transport_error',False);done_count+=1
                    # A truncated/malformed classification is a measured
                    # unresolved outcome, not an infrastructure retry trigger.
                    if transport_errors>=5:raise RuntimeError('Repeated local transport failures; inspect before continuing')
                    submit_next()
                    if done_count%64==0 or done_count==len(jj):
                        print(canonical(dict(model='safeguard',split=split,policy=pid,done=done_count,total=len(jj),errors=errors,transport_errors=transport_errors)),flush=True)
    write(state/f'runtime/safeguard-{split}.json',dict(created_utc=now(),seconds=time.monotonic()-start,
        concurrency=concurrency,vllm='0.31.0',models=model_info,model=MODELS['safeguard'],errors=errors))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--split',required=True,choices=['fit','validation','test'])
    p.add_argument('--concurrency',type=int,default=4);run(**vars(p.parse_args()))
