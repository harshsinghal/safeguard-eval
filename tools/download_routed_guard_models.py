"""Cache pinned open weights without duplicate consolidated or GGUF files."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.routed_guard.common import MODELS

def download():
    from huggingface_hub import snapshot_download
    targets=[(r["model"],r["revision"]) for r in MODELS.values()]
    targets.append((MODELS["kev"]["base"],MODELS["kev"]["base_revision"]))
    for model,revision in targets:
        snapshot_download(model,revision=revision,max_workers=2,
            allow_patterns=["*.json","*.safetensors","*.pt","*.py","*.txt","*.jinja","*.model","README.md","LICENSE"],
            ignore_patterns=["consolidated.safetensors","*.gguf"])
        print("Cached pinned model:",model,revision,flush=True)

if __name__=="__main__":download()
