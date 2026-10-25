"""Verify every planned run against its pinned job, source and data identity."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';sys.path.insert(0,str(repo))
from evals.qwen_policy.run import SETTINGS,sources
from evals.wildguard.metrics import report
from evals.wildguard.run import digest
jobs=[]
for phase in ['pilot','shared','specific','final']:jobs.extend(json.loads((root/(phase+'-jobs.json')).read_text()))
runs=root/'collected';assert {p.parent.name for p in runs.glob('*/summary.json')}=={j['id'] for j in jobs}
files={'pilot.jsonl':root.parent/'wildguard-run/data/pilot.jsonl','fit-search.jsonl':root.parent/'wildguard-run/data/fit-search.jsonl','validation-search.jsonl':root.parent/'wildguard-run/data/validation-search.jsonl','audit-budget.jsonl':root.parent/'wildguard-run/data/audit-budget.jsonl','test.jsonl':root.parent/'wildguard-run/test/test.jsonl'}
verified=[]
for j in jobs:
 p=runs/j['id'];m=json.loads((p/'manifest.json').read_text());s=json.loads((p/'summary.json').read_text());rows=[json.loads(x) for x in (p/'predictions.jsonl').read_text().split('\n') if x.strip()];original=[json.loads(x) for x in files[Path(j['data']).name].read_text().split('\n') if x.strip()];byid={r['id']:r for r in original}
 assert m['model']==j['model'] and m['revision']==j['revision'] and m['stage']==j['stage']
 assert m['sources']==sources() and m['settings']==SETTINGS and m['dataset_sha256']==digest(files[Path(j['data']).name])
 assert m['policy_sha256']==digest(p/'policy.json') and m['ids']==[r['id'] for r in original]
 assert len(rows)==len(original)==len({r['id'] for r in rows}) and s['complete']
 for r in rows:
  src=byid[r['id']]
  assert all(r[k]==v for k,v in src.items() if k!='prompt')
 for k,v in report(rows).items():assert s[k]==v
 if j['stage'] in ('test','audit'):assert m['freeze_sha256']==digest(repo/'published_runs/2026-10-25-qwen/freeze.json')
 verified.append(dict(run=j['id'],n=len(rows),errors=s['errors'],score_coverage=s['valid_answer_score_coverage']))
result=dict(complete=True,total_runs=len(jobs),predictions=sum(x['n'] for x in verified),output_errors=sum(x['errors'] for x in verified),verified_source_population_fields=True,runs=verified)
(repo/'published_runs/2026-10-25-qwen/verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='runs'}))
