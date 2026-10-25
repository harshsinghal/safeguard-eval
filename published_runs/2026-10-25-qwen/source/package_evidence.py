"""Publish only prompt-free evidence and reviewed runtime/source metadata."""
import json,shutil,sys,tarfile,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';pub=repo/'published_runs/2026-10-25-qwen';sys.path.insert(0,str(repo))
from evals.wildguard.export import export
v=json.loads((pub/'verification.json').read_text());b=json.loads((root/'billing.json').read_text());c=json.loads((root/'collection.json').read_text())
assert v['complete'] and c['validated'] and b['status']=='terminated' and b['cumulative_cost_cents']<1000
index=export(root/'collected',pub)
for x in index:x['model']=json.loads((root/'collected'/x['run']/'manifest.json').read_text())['model']
(pub/'run-index.json').write_text(json.dumps(index,indent=2)+'\n')
runtime=pub/'runtime';runtime.mkdir()
with tarfile.open(root/c['archive'],'r:gz') as tar:
 for name in ['runtime-versions.json','environment.txt','vllm-freeze.txt']:
  data=tar.extractfile(name).read()
  if name=='environment.txt':data=('\n'.join(x.rstrip() for x in data.decode().split('\n')).rstrip()+'\n').encode()
  (runtime/name).write_bytes(data)
source=pub/'source';source.mkdir();(source/'evals').mkdir()
for name in ['__init__.py','run.py']:shutil.copyfile(repo/'evals'/name,source/'evals'/name)
for name in ['wildguard','qwen_policy']:shutil.copytree(repo/'evals'/name,source/'evals'/name,ignore=shutil.ignore_patterns('__pycache__','README.md'))
for name in ['serve_and_run.py','prefetch.py','setup.sh','runtime_metadata.py','build_jobs.py','verify.py','package_evidence.py','build_tables.py']:
 shutil.copyfile(root/name,source/name)
(source/'README.md').write_text('# Source snapshot\n\nThe evals package contains the inference, selection, analysis, plotting and CPU reproduction code. Job and launch files record the actual dedicated remote /root layout. Operational packaging helpers retain their original workspace-relative assumptions and are provenance, not a standalone installation command. Use the parent REPRODUCING.md guide and recorded dependency lock.\n')
(source/'jobs').mkdir()
for phase in ['pilot','shared','specific','final']:shutil.copyfile(root/(phase+'-jobs.json'),source/'jobs'/(phase+'-jobs.json'))
for name in ['billing.json','termination.json','ssh-key-removal.json']:shutil.copyfile(root/name,pub/name)
final=json.loads((root/'final-instance.json').read_text());allow=['id','name','status','gpu_type','gpu_count','tier','region','price_per_hour','created_at','ready_at','terminated_at','auto_terminate_hours','auto_terminate_at']
(pub/'final-instance.json').write_text(json.dumps({k:v for k,v in final.items() if k in allow},indent=2)+'\n')
(pub/'private-archive.json').write_text(json.dumps({k:c[k] for k in ['archive','bytes','sha256','validated']},indent=2)+'\n')
shutil.copyfile(repo/'docs/qwen-policy/model-revisions.json',pub/'model-revisions.json')
print(json.dumps(dict(runs=len(index),predictions=sum(x['n'] for x in index))))
