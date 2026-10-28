import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from huggingface_hub import snapshot_download
reg=json.loads(Path('/root/safeguard-eval/evals/hatexplain/registry.json').read_text())
tokenfile=Path('/root/.ensemble_hf_token');token=tokenfile.read_text().strip()
def one(item):
 slug,info=item
 target='/root/models/policylm' if slug=='policylm' else None
 path=snapshot_download(info['model'],revision=info['revision'],local_dir=target,token=token,
  allow_patterns=['*.safetensors','*.json','*.jinja','*.model','*.txt','*.py','*.tiktoken','*.jinja2','*.bpe','vocab*','merges*','README.md'])
 print('Downloaded',slug,flush=True)
 return slug,dict(model=info['model'],revision=info['revision'],path=path)
try:
 with ThreadPoolExecutor(max_workers=3) as pool:values=dict(pool.map(one,reg['models'].items()))
 Path('/root/ensemble-state/checkpoints.json').write_text(json.dumps(values,indent=2)+'\n')
finally:tokenfile.unlink(missing_ok=True)
