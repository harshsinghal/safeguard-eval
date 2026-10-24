import json,subprocess
from pathlib import Path
code="""import json,platform
from importlib.metadata import version,PackageNotFoundError
packages={}
for name in ['torch','transformers','vllm','huggingface-hub','tokenizers','sentencepiece','protobuf']:
 try:packages[name]=version(name)
 except PackageNotFoundError:pass
import torch
print(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),packages=packages,torch_cuda_build=torch.version.cuda)))
"""
result={}
for env in ('policyenv','vllmenv'):
 result[env]=json.loads(subprocess.check_output(['/root/'+env+'/bin/python','-c',code]))
result['native_policylm_actual_workers']=1
result['http_concurrency']=32
result['credential_staging_file_removed']=not Path('/root/.wildguard_hf_token').exists()
Path('/root/runtime-versions.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
