import json,sys,time
from pathlib import Path
sys.path.insert(0,'/root/safeguard-eval')
from evals.activation_probe.common import MODELS,read,rows,write,now
from evals.activation_probe.extract import QwenExtractor
from huggingface_hub import snapshot_download
s=MODELS['qwen'];start=time.monotonic()
p=snapshot_download(s['model'],revision=s['revision'])
e=QwenExtractor(p,read('/root/probe-state/policy.json'))
records=[]
for r in rows('/root/probe-state/inputs/fit.jsonl')[:16]:
 f,m=e.one(r['prompt']);records.append(dict(id=r['id'],shapes={k:list(v.shape) for k,v in f.items()},**m))
write('/root/qwen-smoke.json',dict(created_utc=now(),n=len(records),seconds=time.monotonic()-start,records=records))
print('QWEN_SMOKE_PASSED',len(records),flush=True)
