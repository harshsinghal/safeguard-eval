"""Build explicit stage jobs and an upload manifest, without launching inference."""
import argparse,json
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';reg=repo/'evals/qwen_policy/registry.json';r=json.loads(reg.read_text());remote=Path('/root/safeguard-eval');jobs=[]
p=argparse.ArgumentParser();p.add_argument('phase',choices=['specific','final']);a=p.parse_args()
assert len(r['candidates'])==25
upload=[(str(repo/'evals/qwen_policy'),'safeguard-eval/evals/qwen_policy')]
if a.phase=='specific':
 for model in r['models']:
  for c in [x for x in r['candidates'] if x['model']==model and x['scope']=='model-specific']:
   for split,stage,data in [('fit','search','fit-search.jsonl'),('validation','validation','validation-search.jsonl')]:
    jobs.append(dict(id=c['runs'][split],model=model,revision=r['models'][model]['revision'],stage=stage,data='/root/data/'+data,policy=str(remote/'evals/qwen_policy'/c['path'])))
 assert len(jobs)==20
else:
 pub=repo/'published_runs/2026-10-25-qwen';f=json.loads((pub/'freeze.json').read_text())
 assert f['status']=='frozen' and f['policy_editing_closed']
 upload.extend([(str(pub/'freeze.json'),'safeguard-eval/published_runs/2026-10-25-qwen/freeze.json'),(str(pub/'selection.json'),'safeguard-eval/published_runs/2026-10-25-qwen/selection.json'),(str(root.parent/'wildguard-run/test/test.jsonl'),'data/test.jsonl'),(str(root.parent/'wildguard-run/data/audit-budget.jsonl'),'data/audit-budget.jsonl')])
 for model,meta in f['models'].items():
  for pid in meta['policy_ids']:
   c=next(x for x in r['candidates'] if x['model']==model and json.loads((reg.parent/x['path']).read_text())['id']==pid)
   num=c['runs']['fit'].rsplit('-',1)[-1];slug='qwen-'+model.split('Qwen3.5-')[1].lower()
   for stage,data in [('test','test.jsonl'),('audit','audit-budget.jsonl')]:
    jobs.append(dict(id=slug+'-'+stage+'-'+num,model=model,revision=meta['revision'],stage=stage,data='/root/data/'+data,policy=str(remote/'evals/qwen_policy'/c['path']),freeze=str(remote/'published_runs/2026-10-25-qwen/freeze.json')))
 assert len(jobs)==2*sum(len(x['policy_ids']) for x in f['models'].values())
path=root/(a.phase+'-jobs.json');path.write_text(json.dumps(jobs,indent=2)+'\n');upload.append((str(path),path.name))
(root/(a.phase+'-upload.json')).write_text(json.dumps(upload,indent=2)+'\n');print(a.phase,len(jobs),'jobs')
