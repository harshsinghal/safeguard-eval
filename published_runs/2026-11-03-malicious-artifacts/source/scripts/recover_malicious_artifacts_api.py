#!/usr/bin/env python3
"""Recover cached Jev responses after local storage failure; never issue a request."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.malicious_artifacts.common import verify,read,write,hash_value,canonical,now,TASKS
from evals.malicious_artifacts.infer import jobs,policies_for,prediction
from evals.jev.api import Ledger,parse,billed_cost,RESERVE

p=argparse.ArgumentParser();p.add_argument('--state',required=True);a=p.parse_args()
s=Path(a.state);verify(s,test=True);ledger=Ledger(s/'jev-billing.sqlite')
with ledger.connect() as db:status={uid:st for uid,st in db.execute('SELECT id,status FROM requests')}
recovered=[]
for task in TASKS:
    for pid,policy in policies_for(s,'jev',task,'test').items():
        path,todo,_=jobs(s,'jev',task,'test',pid,policy)
        with path.open('a') as f:
            for job in todo:
                uid=hash_value([task,'test',pid,job['id'],job['request_sha256'],0])
                if uid not in status:continue  # Not yet requested: normal runner will handle it.
                if any(hash_value([task,'test',pid,job['id'],job['request_sha256'],n]) in status for n in (1,2)):
                    raise ValueError('This recovery covers the no-retry storage incident only; inspect retry evidence separately.')
                final=s/f'private-api/{uid}.json';temp=s/f'private-api/{uid}.json.tmp'
                source=final if final.exists() else temp
                try:
                    response=read(source);result=parse(response,['moderation'])['moderation']
                    cost=billed_cost(response)
                except (OSError,ValueError,KeyError,TypeError):
                    response=None;result=dict(prediction='ERROR',score=None,error_type='LocalStorageFailure')
                    cost=RESERVE
                if status[uid]=='pending':ledger.settle(uid,cost,'reported' if response else 'unknown_upper_bound')
                if response:
                    if source==temp:temp.replace(final)
                    result.update(response_model=response.get('model'),response_provider=response.get('provider'),usage=response.get('usage'))
                f.write(canonical(prediction(job,result,'jev'))+'\n');f.flush()
                recovered.append(dict(task=task,policy=pid,id=job['id'],request_sha256=job['request_sha256'],
                    cached_response_recovered=response is not None,temporary_file=source==temp))
ledger.assert_no_pending();write(s/'jev-billing.json',ledger.totals())
write(s/'api-storage-recovery.json',dict(created_utc=now(),incident='Local ENOSPC interrupted saving Jev responses and prediction rows.',
    new_requests=0,policy_or_selection_changes=False,recovered=recovered,all_responses_recovered=all(x['cached_response_recovered'] for x in recovered)))
print(json.dumps(dict(recovered=len(recovered),unrecoverable=sum(not x['cached_response_recovered'] for x in recovered),new_requests=0)))
