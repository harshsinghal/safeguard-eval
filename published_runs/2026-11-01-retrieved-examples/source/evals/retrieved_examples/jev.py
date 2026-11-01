"""One query and one arm per API request; durable reservations cover every attempt."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import threading
import urllib.error
from .common import *
from evals.jev.api import Ledger,RESERVE,read_key,post,parse,billed_cost,save

def run(state,split,keyfile,cap=.6,concurrency=8):
    state=Path(state);verify(state,test=split=='test');key=read_key(keyfile)
    ledger=Ledger(state/'jev-billing.sqlite',cap=cap);ledger.assert_no_pending()
    path=state/f'jobs/jev/{split}.jsonl.gz'
    if digest(path)!=read(state/f'retrieval/{split}-manifest.json')['jobs']['jev']:raise ValueError('Jobs changed')
    jobs=rows(path);raw=state/'private-api'/split;raw.mkdir(parents=True,exist_ok=True);abort=threading.Event()
    def one(job):
        if abort.is_set():raise RuntimeError('Stopped')
        if hash_value(job['body'])!=job['request_sha256']:raise ValueError('Changed request')
        body={'model':MODELS['jev']['model'],'state':{'content':job['body']['content']},
              'questions':{'moderation':job['body']['policy']}}
        if len(canonical(body).encode())+2048>32000:raise ValueError('Conservative request bound exceeded')
        uid=hash_value([split,job['id'],job['arm'],body]);target=raw/(uid+'.json')
        if target.exists():response=read(target)
        else:
            ledger.reserve(uid)
            try:response=post(body,key)
            except urllib.error.HTTPError as exc:
                ledger.settle(uid,RESERVE,'error_upper_bound');abort.set()
                save(raw/(uid+'.error.json'),{'http_status':exc.code})
                raise RuntimeError('Jev HTTP '+str(exc.code)+'; stopped') from None
            except Exception:
                abort.set();raise RuntimeError('Transport error; billing reservation retained') from None
            save(target,response)
            ledger.settle(uid,billed_cost(response))
        parsed=parse(response,['moderation'])['moderation']
        return {**{k:v for k,v in job.items() if k!='body'},**parsed,'model':response['model'],
                'provider':response['provider'],'response_id':response['id'],'api_request_sha256':hash_value(body)}
    result=[]
    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures=[pool.submit(one,j) for j in jobs]
            try:
                for i,f in enumerate(as_completed(futures),1):
                    result.append(f.result())
                    if i%250==0 or i==len(jobs):print(canonical({'model':'jev','split':split,'completed':i,'total':len(jobs),'cost':ledger.totals()['total_accounted_usd']}),flush=True)
            except BaseException:
                abort.set()
                for f in futures:f.cancel()
                raise
    finally:write(state/'jev-costs.json',ledger.totals())
    result.sort(key=lambda r:(r['id'],ARMS.index(r['arm'])))
    write_rows(state/f'predictions/jev/{split}.jsonl',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--split',choices=['smoke','validation','test'],required=True)
    p.add_argument('--keyfile',required=True);p.add_argument('--cap',type=float,default=.6);p.add_argument('--concurrency',type=int,default=8)
    run(**vars(p.parse_args()))
