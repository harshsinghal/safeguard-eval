"""Task-specific supervised baselines. Test is unavailable until all selections freeze."""
import argparse
import math
import time
import numpy as np
from .common import *

def score_rows(rr,scores,slug,pid):
    return [{**metadata(r),'model':slug,'policy_id':pid,'score':float(s),
        'prediction':'BLOCK' if s>=.5 else 'ALLOW'} for r,s in zip(rr,scores)]

def tfidf(state,split):
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    state=Path(state);verify(state,test=split=='test')
    for task in TASKS:
        folder=state/f'learned/tfidf/{task}';folder.mkdir(parents=True,exist_ok=True)
        if split=='validation':
            fit=load_data(state,task,'fit');val=load_data(state,task,'validation');summary={};evidence={}
            for c in (.1,1.,10.):
                pid=f'C{c:g}';model=Pipeline([('tfidf',TfidfVectorizer(analyzer='char',ngram_range=(3,5),
                    max_features=100000,min_df=2,sublinear_tf=True)),('lr',LogisticRegression(C=c,class_weight='balanced',
                    solver='liblinear',max_iter=1000,random_state=SEED))])
                model.fit([r['prompt'] for r in fit],[r['expected']=='BLOCK' for r in fit])
                pred=score_rows(val,model.predict_proba([r['prompt'] for r in val])[:,1],'tfidf',pid)
                path=state/f'predictions/tfidf/{task}/validation/{pid}.jsonl';jsonl(path,pred)
                dest=folder/(pid+'.joblib');joblib.dump(model,dest)
                summary[pid]=measures(pred)
                for p in (path,dest):evidence[str(p.relative_to(state))]=digest(p)
            best=min(summary,key=lambda pid:(-summary[pid]['balanced_accuracy'],-summary[pid]['macro_f1'],float(pid[1:])))
            write(folder/'selection.json',dict(selected=best,validation=summary,evidence=evidence))
        else:
            selected=read(state/'freeze.json')['selected'][task]['tfidf'];test=load_data(state,task,'test')
            model=joblib.load(folder/(selected+'.joblib'))
            jsonl(state/f'predictions/tfidf/{task}/test/{selected}.jsonl',
                score_rows(test,model.predict_proba([r['prompt'] for r in test])[:,1],'tfidf',selected))

def liquid(state,split):
    import torch
    from transformers import AutoTokenizer
    from evals.liquid_finetune.runner import load_model,optimizer_for,batch,infer,seed_all
    torch.set_num_threads(4);state=Path(state);verify(state,test=split=='test')
    tok=AutoTokenizer.from_pretrained(ENCODER['model'],revision=ENCODER['revision'],trust_remote_code=True)
    tok.padding_side='right';start=time.monotonic()
    def encoded(rr):
        ids=[tok(r['prompt'],add_special_tokens=True,truncation=False)['input_ids'] for r in rr]
        if any(len(x)>ENCODER['max_length'] for x in ids):raise ValueError('Encoder overflow; no silent truncation')
        return ids
    for task in TASKS:
        folder=state/f'learned/liquid/{task}';folder.mkdir(parents=True,exist_ok=True)
        if split=='validation':
            fit=load_data(state,task,'fit');val=load_data(state,task,'validation');x=encoded(fit);xv=encoded(val)
            y=np.array([r['expected']=='BLOCK' for r in fit],dtype=np.float32);summary={};evidence={};configs={}
            for rate in ENCODER['learning_rates']:
                model=load_model(SEED);opt=optimizer_for(model,rate)
                steps=math.ceil(len(x)/32)*ENCODER['epochs'];warmup=max(1,math.ceil(steps*.1))
                schedule=torch.optim.lr_scheduler.LambdaLR(opt,lambda step:step/warmup if step<warmup else max(0.,(steps-step)/(steps-warmup)))
                gen=torch.Generator().manual_seed(SEED);initial_head=model.head.weight.detach().cpu().clone()
                tracked=next((n,p) for n,p in model.named_parameters() if n.startswith('backbone.layers.') and n.endswith('weight'))
                initial_backbone=tracked[1].detach().cpu().clone()
                for epoch in range(1,ENCODER['epochs']+1):
                    model.train();opt.zero_grad(set_to_none=True);order=torch.randperm(len(x),generator=gen).tolist();losses=[]
                    # Four-example microbatches bound long-sequence memory; accumulation is 32.
                    for begin in range(0,len(order),4):
                        ix=order[begin:begin+4];window=min(32,len(order)-(begin//32)*32)
                        with torch.autocast('cuda',dtype=torch.bfloat16):
                            logits=model(**batch(tok,x,ix));loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,
                                torch.tensor(y[ix],device='cuda'))
                        if not torch.isfinite(loss):raise ValueError('Nonfinite training loss')
                        (loss*len(ix)/window).backward();losses.append(float(loss.detach()))
                        if (begin+len(ix))%32==0 or begin+len(ix)==len(order):
                            torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
                            opt.step();schedule.step();opt.zero_grad(set_to_none=True)
                    scores,_=infer(model,tok,xv);pid=f'lr{rate:g}-epoch{epoch}'
                    pred=score_rows(val,scores,'liquid',pid);path=state/f'predictions/liquid/{task}/validation/{pid}.jsonl';jsonl(path,pred)
                    dest=folder/(pid+'.pt');torch.save({k:v.detach().cpu() for k,v in model.state_dict().items()},dest)
                    delta=dict(head=float(torch.linalg.vector_norm(model.head.weight.detach().cpu()-initial_head)),
                        backbone=float(torch.linalg.vector_norm(tracked[1].detach().cpu()-initial_backbone)))
                    if min(delta.values())<=0:raise ValueError('Encoder/head did not change')
                    summary[pid]=measures(pred);configs[pid]=dict(rate=rate,epoch=epoch,weight_delta_l2=delta,fit_loss=float(np.mean(losses)))
                    for p in (path,dest):evidence[str(p.relative_to(state))]=digest(p)
                    write(folder/'progress.json',dict(validation=summary,configs=configs))
                    print(canonical(dict(model='liquid',task=task,candidate=pid,validation=summary[pid],seconds=time.monotonic()-start)),flush=True)
                del model,opt,schedule;torch.cuda.empty_cache()
            best=min(summary,key=lambda pid:(-summary[pid]['balanced_accuracy'],-summary[pid]['macro_f1'],configs[pid]['epoch'],configs[pid]['rate']))
            # Only selected weights must survive off GPU; all validation outputs remain.
            selected_weights=folder/(best+'.pt')
            evidence={p:h for p,h in evidence.items() if not p.endswith('.pt') or p==str(selected_weights.relative_to(state))}
            write(folder/'selection.json',dict(selected=best,validation=summary,configs=configs,evidence=evidence,
                fit_n=len(fit),validation_n=len(val),seed=SEED,max_tokens=max(map(len,x+xv))))
            for p in folder.glob('*.pt'):
                if p!=selected_weights:p.unlink()
        else:
            selected=read(state/'freeze.json')['selected'][task]['liquid'];model=load_model(SEED)
            model.load_state_dict(torch.load(folder/(selected+'.pt'),map_location='cpu',weights_only=True),strict=True)
            val=load_data(state,task,'validation');sv,_=infer(model,tok,encoded(val))
            original={r['id']:r for r in complete(state,'liquid',task,'validation',selected)}
            if max(abs(float(s)-original[r['id']]['score']) for r,s in zip(val,sv))>1e-6:raise ValueError('Restored classifier changed')
            test=load_data(state,task,'test');scores,_=infer(model,tok,encoded(test))
            jsonl(state/f'predictions/liquid/{task}/test/{selected}.jsonl',score_rows(test,scores,'liquid',selected))
            del model;torch.cuda.empty_cache()
    write(state/f'runtime/liquid-{split}.json',dict(created_utc=now(),seconds=time.monotonic()-start,
        gpu=torch.cuda.get_device_name(),torch=torch.__version__))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--slug',choices=['tfidf','liquid'],required=True)
    p.add_argument('--split',choices=['validation','test'],required=True);a=p.parse_args();globals()[a.slug](a.state,a.split)
