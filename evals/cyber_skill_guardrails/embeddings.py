"""Full-input frozen Jina features with deterministic token-chunk aggregation."""
import argparse
import time
import numpy as np
from .common import *

def extract(state,split):
    import torch
    from transformers import AutoTokenizer,AutoModel
    state=Path(state);verify(state,test=split=='test');start=time.monotonic();torch.set_num_threads(4)
    tok=AutoTokenizer.from_pretrained(EMBEDDING['model'],revision=EMBEDDING['revision'])
    model=AutoModel.from_pretrained(EMBEDDING['model'],revision=EMBEDDING['revision'],code_revision=EMBEDDING['code_revision'],trust_remote_code=True,torch_dtype=torch.bfloat16).cuda().eval().requires_grad_(False)
    info={}
    for task in TASKS:
        for view in (('package','skill_only') if task=='skills' else ('package',)):
            slug='jina-v2-md' if view=='skill_only' else 'jina-v2'
            for part in (('fit','validation') if split=='development' else ('test',)):
                rr=data(state,task,part);xx=[];counts=[];lengths=[]
                with torch.inference_mode():
                    for i,r in enumerate(rr):
                        text=r['skill_text'] if view=='skill_only' else r['prompt'];ids=tok.encode(text,add_special_tokens=False,truncation=False)
                        if not ids:raise ValueError('Empty embedding input')
                        zz=[];ww=[]
                        for a in range(0,len(ids),4096):
                            chunk=ids[a:a+4096];enc=tok.prepare_for_model(chunk,return_tensors='pt',return_attention_mask=True)
                            enc={k:(v.unsqueeze(0) if v.ndim==1 else v).cuda() for k,v in enc.items() if k in ('input_ids','attention_mask')}
                            h=model(**enc,return_dict=True).last_hidden_state.float();mask=enc['attention_mask'].unsqueeze(-1)
                            z=(h*mask).sum(1)/mask.sum(1);zz.append(z[0]);ww.append(len(chunk))
                        z=(torch.stack(zz)*torch.tensor(ww,device='cuda').unsqueeze(-1)).sum(0)/sum(ww)
                        xx.append(torch.nn.functional.normalize(z,p=2,dim=0).cpu().numpy());counts.append(len(zz));lengths.append(len(ids))
                        if i%128==0 or i+1==len(rr):print(canonical(dict(model=slug,task=task,split=part,completed=i+1,total=len(rr))),flush=True)
                x=np.array(xx,dtype=np.float32)
                if x.shape!=(len(rr),768) or not np.isfinite(x).all():raise ValueError('Invalid features')
                dest=state/f'features/{slug}/{task}/{part}.npz';dest.parent.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(dest,x=x,ids=np.array([r['id'] for r in rr]))
                info[slug+'/'+task+'/'+part]=dict(n=len(rr),view=view,max_tokens=max(lengths),chunk_count=sum(counts),multi_chunk_inputs=sum(n>1 for n in counts),sha256=digest(dest))
    write(state/f'runtime/embeddings-{split}.json',dict(created_utc=now(),seconds=time.monotonic()-start,gpu=torch.cuda.get_device_name(),torch=torch.__version__,features=info))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--split',choices=['development','test'],required=True);a=p.parse_args();extract(a.state,a.split)
