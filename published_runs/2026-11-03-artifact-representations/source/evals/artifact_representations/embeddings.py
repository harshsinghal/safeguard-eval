"""Extract frozen, text-only features; no labels reach the embedding model."""
import argparse
import time
import numpy as np
from .common import *

def extract(state, slug, split):
    import torch
    from transformers import AutoModel, AutoTokenizer
    state=Path(state);verify(state,test=split=='test');spec=MODELS[slug]
    torch.set_num_threads(4);start=time.monotonic()
    tok=AutoTokenizer.from_pretrained(spec['model'],revision=spec['revision'])
    kwargs=dict(revision=spec['revision'],torch_dtype=torch.bfloat16)
    if slug=='jina-v2': kwargs.update(trust_remote_code=True,code_revision=spec['code_revision'])
    else: kwargs['attn_implementation']='sdpa'
    model=AutoModel.from_pretrained(spec['model'],**kwargs).cuda().eval().requires_grad_(False)
    info={}
    for task in TASKS:
        for part in (('fit','validation') if split=='development' else ('test',)):
            rr=data(state,task,part);texts=[r['prompt'] for r in rr]
            prefix='' if slug=='jina-v2' else ('Candidate code snippet:\n' if task=='code' else 'Candidate answer:\n')
            ids=[tok(prefix+t,add_special_tokens=True,truncation=False)['input_ids'] for t in texts]
            if max(map(len,ids))>8192: raise ValueError('Input exceeds extraction limit; do not silently truncate')
            # Sort lengths for padded batches, then restore original order.
            order=sorted(range(len(ids)),key=lambda i:len(ids[i]));out=np.zeros((len(rr),spec['dimension']),np.float32)
            with torch.inference_mode():
                for begin in range(0,len(order),4):
                    ix=order[begin:begin+4]
                    enc=tok.pad({'input_ids':[ids[i] for i in ix]},padding=True,return_tensors='pt').to('cuda')
                    h=model(**enc,return_dict=True).last_hidden_state
                    mask=enc['attention_mask']
                    if slug=='jina-v2': z=(h.float()*mask.unsqueeze(-1)).sum(1)/mask.sum(1).unsqueeze(-1)
                    else: z=h[torch.arange(len(ix),device='cuda'),mask.sum(1)-1].float()
                    out[ix]=torch.nn.functional.normalize(z,p=2,dim=1).cpu().numpy()
            if not np.isfinite(out).all() or np.max(np.abs(np.linalg.norm(out,axis=1)-1))>1e-5: raise ValueError('Invalid embedding')
            dest=state/f'features/{slug}/{task}/{part}.npz';dest.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(dest,x=out,ids=np.array([r['id'] for r in rr]))
            info[task+'/'+part]=dict(n=len(rr),dimension=out.shape[1],max_tokens=max(map(len,ids)),prefix=prefix,sha256=digest(dest))
            print(canonical(dict(model=slug,task=task,split=part,completed=len(rr))),flush=True)
    write(state/f'runtime/{slug}-{split}.json',dict(created_utc=now(),seconds=time.monotonic()-start,
        gpu=torch.cuda.get_device_name(),torch=torch.__version__,parameter_count=sum(p.numel() for p in model.parameters()),features=info))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--slug',choices=['jina-v2','jina-code'],required=True)
    p.add_argument('--split',choices=['development','test'],required=True);a=p.parse_args();extract(a.state,a.slug,a.split)
