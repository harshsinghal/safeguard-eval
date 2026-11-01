import json,hashlib,os
from pathlib import Path
from huggingface_hub import hf_hub_download
state=Path('/root/cloud-shield-hf');r=json.loads((state/'registration.json').read_text())['model']
target=Path(r['model']);target.mkdir(exist_ok=False)
files=['config.json','generation_config.json','model.safetensors','tokenizer.json','tokenizer_config.json','chat_template.jinja','processor_config.json']
manifest={}
for name in files:
 p=Path(hf_hub_download(r['source_model'],name,revision=r['revision']))
 (target/name).symlink_to(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 manifest[name]=dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
(state/'hf-files.json').write_text(json.dumps(dict(source_model=r['source_model'],revision=r['revision'],files=manifest,no_tensor_conversion=True),indent=2)+'\n')
print('Pinned HF-only snapshot prepared and checksummed.',flush=True)
