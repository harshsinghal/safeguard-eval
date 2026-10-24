import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from huggingface_hub import snapshot_download
revisions=json.loads(Path('/root/safeguard-eval/evals/wildguard/revisions.json').read_text())
token=Path('/root/.wildguard_hf_token').read_text().strip()
def one(item):
 repo,info=item
 if repo=='dataset':return
 target='/root/models/policylm' if repo=='musubilabs/policylm-1.7b' else None
 snapshot_download(repo,revision=info['revision'],local_dir=target,token=token)
 print('Downloaded',repo,flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,revisions.items()))
Path('/root/.wildguard_hf_token').unlink()
