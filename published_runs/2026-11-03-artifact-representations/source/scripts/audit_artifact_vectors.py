# Numerical reproducibility check only. Never changes selection or predictions.
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from transformers import AutoModel,AutoTokenizer
from evals.artifact_representations.common import MODELS,rows,hash_value,write
p=argparse.ArgumentParser();p.add_argument('--slug',required=True);p.add_argument('--state',required=True);a=p.parse_args();slug=a.slug
s=Path(a.state);spec=MODELS[slug];torch.set_num_threads(4)
t=AutoTokenizer.from_pretrained(spec['model'],revision=spec['revision']);kwargs=dict(revision=spec['revision'],torch_dtype=torch.bfloat16)
if slug=='jina-v2':kwargs.update(trust_remote_code=True,code_revision=spec['code_revision'])
else:kwargs['attn_implementation']='sdpa'
m=AutoModel.from_pretrained(spec['model'],**kwargs).cuda().eval().requires_grad_(False);out={}
for task in ('code','skills'):
 rr=rows(s/f'data/{task}/validation.jsonl');f=np.load(s/f'features/{slug}/{task}/validation.npz',allow_pickle=False)
 assert f['ids'].tolist()==[r['id'] for r in rr]
 ix=sorted(range(len(rr)),key=lambda i:hash_value(rr[i]['id']))[:16];new=[]
 prefix='' if slug=='jina-v2' else ('Candidate code snippet:\n' if task=='code' else 'Candidate answer:\n')
 with torch.inference_mode():
  for i in ix:
   e=t(prefix+rr[i]['prompt'],return_tensors='pt',truncation=False).to('cuda');h=m(**e,return_dict=True).last_hidden_state
   if slug=='jina-v2':z=(h.float()*e['attention_mask'].unsqueeze(-1)).sum(1)/e['attention_mask'].sum(1).unsqueeze(-1)
   else:z=h[:,-1].float()
   new.append(torch.nn.functional.normalize(z,p=2,dim=1).cpu().numpy()[0])
 new=np.array(new);old=f['x'][ix];cos=(new*old).sum(1);maxerr=float(np.max(np.abs(new-old)))
 out[task]=dict(n=len(ix),ids=[rr[i]['id'] for i in ix],min_cosine=float(cos.min()),mean_cosine=float(cos.mean()),max_component_difference=maxerr,comparison='Fresh model load, singleton batch versus original length-sorted batch4; validation inputs only',passed=bool(cos.min()>=.999 and maxerr<=.005))
write(s/f'runtime/{slug}-vector-stability.json',out);print(json.dumps(out));assert all(x['passed'] for x in out.values())
