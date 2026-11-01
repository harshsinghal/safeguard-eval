import argparse
from pathlib import Path
import numpy as np
from .common import *

class Encoder:
    def __init__(self):
        import torch
        from transformers import AutoModel,AutoTokenizer
        self.torch=torch;torch.set_num_threads(4)
        self.tok=AutoTokenizer.from_pretrained(ENCODER['model'],revision=ENCODER['revision'])
        self.model=AutoModel.from_pretrained(ENCODER['model'],revision=ENCODER['revision']).eval().requires_grad_(False)
        self.prefix=self.tok.encode('query: ',add_special_tokens=False)

    def encode(self,texts):
        torch=self.torch;windows=[];owners=[];weights=[];counts=[]
        for i,text in enumerate(texts):
            ids=self.tok.encode(text,add_special_tokens=False,truncation=False)
            chunks=[ids[j:j+500] for j in range(0,len(ids),500)] or [[]]
            counts.append(len(chunks))
            for chunk in chunks:
                windows.append({'input_ids':self.tok.build_inputs_with_special_tokens(self.prefix+chunk)})
                owners.append(i);weights.append(max(len(chunk),1))
        acc=np.zeros((len(texts),384),np.float64);tot=np.zeros(len(texts))
        with torch.inference_mode():
            for j in range(0,len(windows),32):
                b=self.tok.pad(windows[j:j+32],padding=True,return_tensors='pt')
                h=self.model(**b).last_hidden_state
                mask=b['attention_mask'][...,None]
                v=(h*mask).sum(1)/mask.sum(1)
                v=torch.nn.functional.normalize(v,p=2,dim=1).numpy()
                for k,x in enumerate(v,j):acc[owners[k]]+=x*weights[k];tot[owners[k]]+=weights[k]
        acc/=tot[:,None]
        acc/=np.maximum(np.linalg.norm(acc,axis=1,keepdims=True),1e-12)
        return acc.astype(np.float32),counts

def run(state,split):
    state=Path(state);reg=verify(state,test=split=='test')
    target=state/f'retrieval/{split}.jsonl.gz'
    if target.exists():raise ValueError('Immutable retrieval already exists')
    bank=rows(state/'private-bank.jsonl');byid={r['id']:r for r in bank}
    encoder=Encoder();folder=state/'private-embeddings';folder.mkdir(exist_ok=True)
    p=folder/'bank.npy'
    if p.exists():
        if read(folder/'bank.json')['sha256']!=digest(p):raise ValueError('Embedding cache changed')
        bx=np.load(p,allow_pickle=False)
    else:
        bx,counts=encoder.encode([r['prompt'] for r in bank]);np.save(p,bx,allow_pickle=False)
        write(folder/'bank.json',{'sha256':digest(p),'encoder':ENCODER,'windows':counts,'bank_sha256':digest(state/'private-bank.jsonl')})
    query=rows(state/f'inputs/{split}.jsonl')
    qx,counts=encoder.encode([r['prompt'] for r in query]);np.save(folder/f'{split}.npy',qx,allow_pickle=False)
    smoke_groups={r['id']:r['group'] for r in rows(state/'metadata/smoke.jsonl.gz')} if split=='smoke' else {}
    retrieval=[];votes=[];jobs={m:[] for m in MODELS}
    for q,vec,nwin in zip(query,qx,counts):
        excluded=[r['id'] for r in bank if r['group']==smoke_groups.get(q['id'])] if split=='smoke' else []
        rr=retrieve(vec,bx,bank,excluded)
        rr.update({'id':q['id'],'prompt_sha256':q['prompt_sha256'],'query_windows':nwin})
        retrieval.append(rr);votes.append({'id':q['id'],'prediction':vote(rr['nearest_four'],byid),'prompt_sha256':q['prompt_sha256']})
        choices={'policy_only':[],'fixed_four':reg['fixed_ids'],**{a:[r['id'] for r in rr[a]] for a in ARMS[2:]}}
        for model in MODELS:
            base=read(state/f'policies/{model}.json')
            for arm in ARMS:jobs[model].append(build_job(q,model,arm,base,choices[arm],byid))
    write_rows(target,retrieval);write_rows(state/f'predictions/knn/{split}.jsonl.gz',votes)
    for model,rr in jobs.items():write_rows(state/f'jobs/{model}/{split}.jsonl.gz',rr)
    write(state/f'retrieval/{split}-manifest.json',{'encoder':ENCODER,'retrieval_sha256':digest(target),
        'input_sha256':digest(state/f'inputs/{split}.jsonl'),'bank_sha256':digest(state/'private-bank.jsonl'),
        'jobs':{m:digest(state/f'jobs/{m}/{split}.jsonl.gz') for m in MODELS},
        'query_window_counts':dict(__import__('collections').Counter(counts)),'created_utc':now()})
    print(canonical({'split':split,'queries':len(query),'classifications_per_model':4*len(query),'query_windows':sum(counts)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--split',choices=['smoke','validation','test'],required=True)
    run(**vars(p.parse_args()))
