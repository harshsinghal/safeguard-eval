import gzip,hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';pub=repo/'published_runs/2026-10-25-qwen'
allowed={'id','source_index','prompt_sha256','expected','split','adversarial','subcategory','agreement','group','normalized_sha256','request_sha256','prediction','score','error_type','latency_seconds','usage'}
rows=0
for p in pub.glob('runs/*/predictions.jsonl.gz'):
 for line in gzip.decompress(p.read_bytes()).decode().split('\n'):
  if not line.strip():continue
  d=json.loads(line);assert set(d)<=allowed;rows+=1
assert rows==json.loads((pub/'verification.json').read_text())['predictions']
for p in pub.rglob('*'):
 if not p.is_file():continue
 assert p.name not in {'private-raw.jsonl','api.py','id_ed25519','id_ed25519.pub','.env'}
 if p.suffix in {'.json','.py','.md','.txt','.sh'}:
  data=p.read_text()
  assert not re.search(r'\bhf_[A-Za-z0-9]{25,}\b|\bsk-[A-Za-z0-9_-]{30,}\b|-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----',data),str(p)
checks=[]
for p in sorted(pub.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS':checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(pub)))
(pub/'SHA256SUMS').write_text('\n'.join(checks)+'\n')
for entry in (pub/'SHA256SUMS').read_text().splitlines():
 h,name=entry.split('  ',1);assert hashlib.sha256((pub/name).read_bytes()).hexdigest()==h
print(json.dumps(dict(prompt_free_predictions=rows,checksummed_files=len(checks),secret_pattern_scan='passed')))
