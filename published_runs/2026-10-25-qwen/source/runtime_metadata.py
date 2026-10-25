import importlib.metadata,json,platform,subprocess
from pathlib import Path
packages={}
for name in ['vllm','torch','transformers','huggingface_hub','tokenizers','sentencepiece','protobuf','flashinfer-python']:
 try:packages[name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:packages[name]=None
r=dict(python=platform.python_version(),platform=platform.platform(),packages=packages,
       gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader']).decode().strip(),
       credential_staged=False,model_downloads='Public pinned snapshots, anonymous Hugging Face access')
Path('/root/runtime-versions.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
