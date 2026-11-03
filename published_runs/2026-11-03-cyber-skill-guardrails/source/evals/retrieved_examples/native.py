"""Pinned native classifiers; no learned cutoff or score calibration."""
import argparse
import gc
import math
from pathlib import Path
import sys
import time
from .common import *

class Engine:
    def __init__(self,model,vendor=None):
        import torch
        from huggingface_hub import snapshot_download
        self.torch=torch;self.slug=model;torch.set_num_threads(4)
        self.spec=MODELS[model]
        if model=='kev':
            from evals.decision_models.adapters import Adapter
            self.native=Adapter('kev',vendor,serving_fused=True)
            return
        path=snapshot_download(self.spec['model'],revision=self.spec['revision'],
            ignore_patterns=['consolidated.safetensors','*.pt','*.pth'])
        if model=='policylm':
            sys.path.insert(0,str(Path(path)/'inference'))
            from policylm_infer import PolicyLM,Policy,Category
            self.Policy,self.Category=Policy,Category
            self.native=PolicyLM.from_pretrained(path,device='cuda',dtype='bfloat16',max_batch_rows=1,max_chars=None)
        else:
            from transformers import AutoTokenizer,Mistral3ForConditionalGeneration
            self.tok=AutoTokenizer.from_pretrained(path);self.tok.padding_side='left'
            if self.tok.pad_token_id is None:self.tok.pad_token=self.tok.eos_token
            self.model=Mistral3ForConditionalGeneration.from_pretrained(path,dtype=torch.bfloat16,
                attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
            self.labels=[self.tok.encode(t,add_special_tokens=False) for t in ('yes','no')]
            if any(len(x)!=1 for x in self.labels):raise ValueError('Non-single-token labels')
            self.labels=[x[0] for x in self.labels]

    def encode(self,job):
        body=job['body'];p=body['policy'];text=body['content']
        if self.slug=='kev':return self.native.encode(text,p)
        if self.slug=='policylm':
            policy=self.Policy([self.Category(p['name'],violation_rule=p['block'],
                not_violation_rule=p['allow'],exception_override=p['precedence'])])
            self.native.check_policy(policy)
            return text,policy,p['name']
        from evals.run import build_payload
        messages=build_payload('shieldstral',self.spec['model'],p,text)['messages']
        ids=self.tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
        if hasattr(ids,'keys'):ids=ids['input_ids']
        if len(ids)>16384:raise ValueError('Context limit; no truncation')
        return ids

    def forward(self,enc):
        torch=self.torch
        with torch.inference_mode():
            if self.slug=='kev':return self.native.forward(enc)
            if self.slug=='policylm':
                out=[]
                for text,policy,name in enc:
                    result=self.native.classify(text,policy,cutoff=.5)
                    s=float(result.categories[name].score)
                    out.append({'score':s,'prediction':'BLOCK' if s>=.5 else 'ALLOW',
                        'windows':result.windows,'variants':result.variants,'cleaned':result.cleaned})
                return out
            batch=self.tok.pad([{'input_ids':x} for x in enc],padding=True,return_tensors='pt')
            batch={k:v.cuda() for k,v in batch.items()}
            h=self.model.model.language_model(**batch,use_cache=False,return_dict=True).last_hidden_state[:,-1,:]
            logits=self.model.lm_head(h).float()
            pair=logits[:,self.labels];scores=pair.softmax(-1)[:,0].cpu().tolist()
            top=logits.argmax(-1).cpu().tolist()
            return [{'score':s,'prediction':'BLOCK' if s>=.5 else 'ALLOW','top_token_is_label':t in self.labels} for s,t in zip(scores,top)]

def run(state,model,split,vendor=None,batch_size=8):
    state=Path(state);verify(state,test=split=='test')
    path=state/f'jobs/{model}/{split}.jsonl.gz';expected=read(state/f'retrieval/{split}-manifest.json')['jobs'][model]
    if digest(path)!=expected:raise ValueError('Jobs changed')
    jobs=rows(path);out=state/f'predictions/{model}/{split}.jsonl'
    out.parent.mkdir(parents=True,exist_ok=True)
    existing=rows(out) if out.exists() else []
    done={(r['id'],r['arm']):r for r in existing}
    if len(done)!=len(existing):raise ValueError('Duplicate cached results')
    for j in jobs:
        if hash_value(j['body'])!=j['request_sha256']:raise ValueError('Changed request')
        old=done.get((j['id'],j['arm']))
        if old and old['request_sha256']!=j['request_sha256']:raise ValueError('Cache mismatch')
    engine=Engine(model,vendor);pending=[j for j in jobs if (j['id'],j['arm']) not in done]
    size=1 if model=='policylm' else batch_size
    if split=='smoke':
        sample=jobs[:min(16,len(jobs))];enc=[engine.encode(j) for j in sample]
        serial=[engine.forward([x])[0] for x in enc]
        batched=[]
        for i in range(0,len(enc),size):batched+=engine.forward(enc[i:i+size])
        diff=max(abs(a['score']-b['score']) for a,b in zip(serial,batched))
        changes=sum(a['prediction']!=b['prediction'] for a,b in zip(serial,batched))
        write(state/f'runtime/{model}-parity.json',{'n':len(enc),'max_score_difference':diff,'decision_changes':changes,'batch_size':size})
        if changes or diff>.005:raise ValueError('Batch parity gate failed; document before changing batch size')
    start=time.monotonic()
    with out.open('a') as f:
        for i in range(0,len(pending),size):
            batch=pending[i:i+size]
            encoded=[engine.encode(j) for j in batch]
            results=engine.forward(encoded)
            if len(results)!=len(batch):raise ValueError('Missing result')
            for j,r in zip(batch,results):
                if not math.isfinite(r['score']) or not 0<=r['score']<=1 or r['prediction'] not in ('ALLOW','BLOCK'):
                    raise ValueError('Invalid native result')
                record={k:v for k,v in j.items() if k!='body'}
                record.update(r);record['model']=MODELS[model]
                f.write(canonical(record)+'\n')
            f.flush()
            if (i//size)%64==0 or i+size>=len(pending):print(canonical({'model':model,'split':split,'done':min(i+size,len(pending))+len(done),'total':len(jobs)}),flush=True)
    write(state/f'runtime/{model}-{split}.json',{'n':len(jobs),'torch':engine.torch.__version__,
        'gpu':engine.torch.cuda.get_device_name(),'batch_size':size,'seconds':time.monotonic()-start,
        'prediction_sha256':digest(out),'created_utc':now()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--model',choices=['policylm','shieldstral','kev'],required=True)
    p.add_argument('--split',choices=['smoke','validation','test'],required=True);p.add_argument('--vendor');p.add_argument('--batch-size',type=int,default=8)
    run(**vars(p.parse_args()))
