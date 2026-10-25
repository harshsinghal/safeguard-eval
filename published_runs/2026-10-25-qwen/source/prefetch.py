import json,time
from pathlib import Path
from huggingface_hub import snapshot_download
root=Path('/root');reg=json.loads((root/'safeguard-eval/evals/qwen_policy/registry.json').read_text())
for model,meta in reg['models'].items():
    started=time.time();print('DOWNLOAD',model,meta['revision'],flush=True)
    path=snapshot_download(model,revision=meta['revision'],max_workers=4,
        allow_patterns=['*.safetensors','*.json','*.jinja','tokenizer.model','vocab.*','merges.txt','README.md'])
    (root/(model.split('/')[-1]+'.ready.json')).write_text(json.dumps(dict(model=model,revision=meta['revision'],path=path,seconds=time.time()-started)))
    print('READY',model,flush=True)
