"""Portable CPU encoder plus routing head, optionally dynamic INT8 linear layers."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import torch
from torch import nn
from .common import *

class EncoderClassifier(nn.Module):
    def __init__(self,body):
        super().__init__(); self.body=body
        self.head=nn.Linear(body.config.hidden_size,len(CATEGORIES))
        nn.init.normal_(self.head.weight,std=.02); nn.init.zeros_(self.head.bias)

    def forward(self,input_ids,attention_mask):
        hidden=self.body(input_ids=input_ids,attention_mask=attention_mask,use_cache=False,return_dict=True).last_hidden_state
        mask=attention_mask.unsqueeze(-1).float()
        pooled=(hidden.float()*mask).sum(1)/mask.sum(1).clamp_min(1)
        return self.head(pooled)

    def save(self,path,tokenizer,metadata):
        from safetensors.torch import save_file
        path=Path(path); path.mkdir(parents=True,exist_ok=False)
        self.body.save_pretrained(path/"backbone",safe_serialization=True)
        # The nested body is not registered by AutoModelForMaskedLM for code copying.
        import inspect,shutil
        code=Path(inspect.getfile(type(self.body)))
        shutil.copyfile(code,path/"backbone"/code.name)
        tokenizer.save_pretrained(path/"tokenizer")
        save_file({k:v.detach().cpu().contiguous() for k,v in self.head.state_dict().items()},path/"head.safetensors")
        write(path/"router.json",dict(metadata,categories=CATEGORIES,max_tokens=MAX_TOKENS,
            label_scope="benchmark-family membership, not harm or complete semantic applicability",model=MODEL,revision=REVISION))


def load_initial(device="cpu"):
    from transformers import AutoModelForMaskedLM,AutoTokenizer
    torch.manual_seed(SEED)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=True)
    mlm,info=AutoModelForMaskedLM.from_pretrained(MODEL,revision=REVISION,trust_remote_code=True,
        dtype=torch.float32,attn_implementation="sdpa",output_loading_info=True)
    if any(info.get(key) for key in ("missing_keys","unexpected_keys","mismatched_keys","error_msgs")):
        raise ValueError("Pretrained Liquid weights did not load exactly: "+str(info))
    body=mlm.lfm2
    del mlm
    return EncoderClassifier(body).to(device),tokenizer


def encode(tokenizer,text):
    if not isinstance(text,str) or not text.strip() or len(text.encode())>1024*1024:
        raise ValueError("Expected nonempty text <=1 MiB")
    ids=tokenizer(text,add_special_tokens=True,truncation=False)["input_ids"]
    return bounded_tokens(ids),len(ids)


def batch(tokenizer,encoded,device):
    return {k:v.to(device) for k,v in tokenizer.pad(
        [dict(input_ids=ids,attention_mask=[1]*len(ids)) for ids in encoded],padding=True,return_tensors="pt").items()
        if k in ("input_ids","attention_mask")}


class Router:
    def __init__(self,path,threads=4,int8=False):
        from transformers import AutoModel,AutoTokenizer
        from safetensors.torch import load_file
        if not 1<=threads<=16: raise ValueError("Use 1..16 CPU threads")
        torch.set_num_threads(threads)
        path=Path(path); self.config=read(path/"router.json")
        if self.config["categories"]!=CATEGORIES or self.config["max_tokens"]!=MAX_TOKENS:
            raise ValueError("Incompatible routing contract")
        self.tokenizer=AutoTokenizer.from_pretrained(path/"tokenizer",local_files_only=True)
        body,info=AutoModel.from_pretrained(path/"backbone",trust_remote_code=True,local_files_only=True,
            dtype=torch.float32,attn_implementation="sdpa",output_loading_info=True)
        if any(info.get(key) for key in ("missing_keys","unexpected_keys","mismatched_keys","error_msgs")):
            raise ValueError("Classifier encoder checkpoint did not load exactly: "+str(info))
        self.model=EncoderClassifier(body)
        self.model.head.load_state_dict(load_file(path/"head.safetensors"),strict=True)
        self.model.eval()
        if int8:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",DeprecationWarning)
                self.model=torch.ao.quantization.quantize_dynamic(self.model,{nn.Linear},dtype=torch.qint8)
        self.int8=int8

    def predict(self,text):
        ids,original=encode(self.tokenizer,text)
        with torch.inference_mode():
            logits=self.model(**batch(self.tokenizer,[ids],"cpu"))[0].float().numpy()
        logits=logits/float(self.config.get("temperature",1.))
        exp=np.exp(logits-logits.max()); probabilities=exp/exp.sum()
        candidates=rank_candidates(probabilities,int(self.config.get("candidate_count",2)))
        return dict(candidate_categories=candidates,
            category_probabilities={c:float(p) for c,p in zip(CATEGORIES,probabilities)},
            fallback_required=bool(probabilities.max()<self.config.get("fallback_below",.6)),
            original_tokens=original,used_tokens=len(ids),truncated=original>MAX_TOKENS,
            moderation_decision=None,precision="dynamic_int8" if self.int8 else "float32")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--checkpoint",required=True);p.add_argument("--text",required=True)
    p.add_argument("--int8",action="store_true");p.add_argument("--threads",type=int,default=4)
    a=p.parse_args();print(json.dumps(Router(a.checkpoint,a.threads,a.int8).predict(a.text),indent=2))
