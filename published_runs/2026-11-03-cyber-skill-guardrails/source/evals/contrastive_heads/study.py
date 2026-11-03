"""Fit on training, select on validation, freeze, then score the public tests."""
import argparse
import json
import time
import warnings
import numpy as np
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from .common import *
from .learn import standardize,linear,neural,neural_predict
from evals.leaderboard.metrics import metrics,bootstrap,THRESHOLDS

PROFILES=['balanced','accuracy','false_block_limit','catch_target']

def selections(y,candidates):
    selected={k:None for k in PROFILES};grid=[]
    for cid,c in sorted(candidates.items()):
        for t in THRESHOLDS:
            mm=[metrics(y,np.asarray(s)>=t) for s in c['scores']]
            avg={k:float(np.mean([m[k] for m in mm])) for k in ['balanced_accuracy','accuracy','recall','specificity','macro_f1','false_positive_rate']}
            minimum=float(np.mean([min(m['recall'],m['specificity']) for m in mm]))
            tail=(-minimum,-avg['macro_f1'],abs(t-.5),t,cid)
            row=dict(candidate=cid,threshold=t,mean_validation=avg,seed_validation=mm)
            grid.append(dict(candidate=cid,threshold=t,**avg))
            for p in PROFILES:
                if p=='false_block_limit' and any(m['false_positive_rate']>.05+1e-12 for m in mm):continue
                if p=='catch_target' and any(m['recall']<.90-1e-12 for m in mm):continue
                key={'balanced':(-avg['balanced_accuracy'],),'accuracy':(-avg['accuracy'],),
                     'false_block_limit':(-avg['recall'],avg['false_positive_rate']),
                     'catch_target':(avg['false_positive_rate'],-avg['recall'])}[p]+tail
                if selected[p] is None or key<selected[p]['rank_key']:
                    selected[p]=dict(**row,rank_key=key)
    return selected,grid

def train(state,ds,backend):
    import torch
    state=Path(state);check_registration(state)
    if (state/'freeze.json').exists():raise ValueError('Study already frozen')
    folder=state/'fits'/ds/backend
    if (folder/'validation.json').exists():raise ValueError('Fit already completed')
    folder.mkdir(parents=True,exist_ok=True)
    fm,x,_=load(state,ds,backend,'fit');vm,xv,_=load(state,ds,backend,'validation')
    y,yv=labels(fm),labels(vm);scaler,x,xv=standardize(x,xv)
    np.savez(folder/'scaler.npz',mean=scaler.mean_,scale=scaler.scale_)
    candidates={};failed=[];start=time.monotonic()
    for c in CS:
        cid=f'lr-c{c:g}'
        try:clf,s=linear(x,y,xv,c)
        except ConvergenceWarning:
            failed.append(dict(candidate=cid,error='ConvergenceWarning'));continue
        p=folder/(cid+'.npz');np.savez(p,coef=clf.coef_[0],intercept=clf.intercept_[0])
        candidates[cid]=dict(head='lr',C=c,seeds=[SEEDS[0]],scores=[s.tolist()],
            parameters=[str(p.relative_to(state))],iterations=int(clf.n_iter_[0]))
    for head in ['mlp','contrastive']:
        for decay in DECAYS:
            for seed in SEEDS:
                for epoch,params,s,history in neural(x,y,xv,decay,seed,head=='contrastive'):
                    cid=f'{head}-wd{decay:g}-e{epoch:02d}'
                    p=folder/(cid+f'-s{seed}.pt');torch.save(params,p)
                    if cid not in candidates:
                        candidates[cid]=dict(head=head,weight_decay=decay,epoch=epoch,seeds=[],scores=[],parameters=[],history=[])
                    record=candidates[cid];record['seeds'].append(seed);record['scores'].append(s.tolist())
                    record['parameters'].append(str(p.relative_to(state)));record['history'].append(history)
                print('TRAINED',ds,backend,head,decay,seed,round(time.monotonic()-start,1),flush=True)
    choices={};grids={}
    for head in ['lr','mlp','contrastive']:
        choices[head],grids[head]=selections(yv,{k:c for k,c in candidates.items() if c['head']==head})
    write(folder/'validation.json',dict(dataset=ds,backend=backend,metadata=vm,candidates=candidates,
        choices=choices,grids=grids,failed_candidates=failed,seconds=time.monotonic()-start),exclusive=True)
    print('SELECTED',ds,backend,{h:{p:(v['candidate'],v['threshold'],round(v['mean_validation']['balanced_accuracy'],4)) if v else None for p,v in q.items()} for h,q in choices.items()},flush=True)

def freeze(state):
    state=Path(state);check_registration(state);choices={};hashes={};overall={}
    for ds in DATASETS:
        choices[ds]={}
        for backend in BACKENDS:
            f=state/'fits'/ds/backend;v=read(f/'validation.json')
            choices[ds][backend]=v['choices']
            for p in sorted(f.iterdir()):
                if p.is_file():hashes[str(p.relative_to(state))]=digest(p)
            for split in ['fit','validation']:
                load(state,ds,backend,split)
                for p in sorted((state/'features'/ds/backend/split).iterdir()):
                    if p.is_file():hashes[str(p.relative_to(state))]=digest(p)
        overall[ds]={}
        for profile in ['balanced','accuracy']:
            options=[(c['rank_key'],backend,head) for backend,ch in choices[ds].items() for head,cc in ch.items() if (c:=cc[profile]) is not None]
            _,backend,head=min(options)
            overall[ds][profile]=dict(backend=backend,head=head)
    write(state/'freeze.json',dict(created_utc=now(),sources=sources(),hashes=hashes,choices=choices,
        overall=overall,registration_sha256=digest(state/'registration.json'),
        note='No test score or test label used for fitting or selection; public test previously examined in earlier studies.'),exclusive=True)
    print('FROZEN',overall,flush=True)

def score(y,p,s):
    m=metrics(y,p,s);ss=np.clip(s,1e-7,1-1e-7)
    m.update(brier=float(np.mean((ss-y)**2)),log_loss=float(-np.mean(y*np.log(ss)+(1-y)*np.log(1-ss))))
    return m

def evaluate(state):
    import torch
    state=Path(state);f=check_freeze(state)
    if (state/'results.json').exists():raise ValueError('Immutable test evaluation exists')
    results={};predictions={}
    for ds in DATASETS:
        results[ds]=dict(profiles={p:{} for p in PROFILES});predictions[ds]={};primary={};meta=None
        for backend in BACKENDS:
            meta,raw,_=load(state,ds,backend,'test');y=labels(meta)
            folder=state/'fits'/ds/backend;v=read(folder/'validation.json')
            scale=np.load(folder/'scaler.npz',allow_pickle=False)
            x=((raw-scale['mean'])/scale['scale']).astype(np.float32)
            cache={}
            for head,profiles in f['choices'][ds][backend].items():
                key=backend+'/'+head;predictions[ds][key]={}
                for profile,c in profiles.items():
                    if c is None:results[ds]['profiles'][profile][key]=None;continue
                    cid=c['candidate'];can=v['candidates'][cid]
                    if cid not in cache:
                        scores=[]
                        for path in can['parameters']:
                            if head=='lr':
                                params=np.load(state/path,allow_pickle=False);s=expit(x@params['coef']+params['intercept'])
                            else:s=neural_predict(torch.load(state/path,map_location='cpu',weights_only=True),x)
                            scores.append(s)
                        cache[cid]=scores
                    ss=cache[cid];pp=[(s>=c['threshold']).astype(int) for s in ss];mm=[score(y,p,s) for p,s in zip(pp,ss)]
                    summary={k:dict(mean=float(np.mean([m[k] for m in mm])),min=float(min(m[k] for m in mm)),max=float(max(m[k] for m in mm)))
                             for k in ['accuracy','balanced_accuracy','false_blocks','missed_violations']}
                    results[ds]['profiles'][profile][key]=dict(selection=c,seeds=can['seeds'],seed_metrics=mm,summary=summary)
                    predictions[ds][key][profile]=dict(scores=[s.tolist() for s in ss],predictions=[p.tolist() for p in pp],seeds=can['seeds'])
                    if profile=='balanced':primary[key]=pp[0]
        boot=bootstrap(meta,primary);pairs=[]
        for backend in BACKENDS:
            for a,b in [('mlp','lr'),('contrastive','mlp'),('contrastive','lr')]:
                aa,bb=backend+'/'+a,backend+'/'+b;delta=boot[aa]['balanced_accuracy']-boot[bb]['balanced_accuracy']
                ma=results[ds]['profiles']['balanced'][aa]['seed_metrics'][0];mb=results[ds]['profiles']['balanced'][bb]['seed_metrics'][0]
                pairs.append(dict(method=aa,comparator=bb,balanced_accuracy_delta=ma['balanced_accuracy']-mb['balanced_accuracy'],
                    ci95=np.quantile(delta,[.025,.975]).tolist(),false_blocks_delta=ma['false_blocks']-mb['false_blocks'],
                    misses_delta=ma['missed_violations']-mb['missed_violations'],
                    corrected=int(((primary[aa]==y)&(primary[bb]!=y)).sum()),newly_wrong=int(((primary[aa]!=y)&(primary[bb]==y)).sum())))
        results[ds]['paired_contrasts']=pairs
        results[ds]['ci95']={k:{m:np.nanquantile(vals,[.025,.975]).tolist() for m,vals in vv.items()} for k,vv in boot.items()}
        results[ds]['slices']={}
        for field in (['subcategory','adversarial'] if ds=='wildguard' else ['source_label','agreement','platform']):
            results[ds]['slices'][field]={}
            for value in sorted({str(r.get(field)) for r in meta}):
                mask=np.asarray([str(r.get(field))==value for r in meta]);results[ds]['slices'][field][value]={k:metrics(y[mask],p[mask]) for k,p in primary.items()}
        predictions[ds]['metadata']=meta
    write(state/'test-predictions.json',predictions,exclusive=True)
    write(state/'results.json',dict(created_utc=now(),freeze_sha256=digest(state/'freeze.json'),overall=f['overall'],results=results),exclusive=True)
    for ds,rr in results.items():
        for key,row in rr['profiles']['balanced'].items():
            m=row['seed_metrics'][0];print(ds,key,'accuracy',round(m['accuracy']*100,3),'BA',round(m['balanced_accuracy']*100,3),'FP',m['false_blocks'],'FN',m['missed_violations'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','freeze','evaluate']);p.add_argument('--state',required=True)
    p.add_argument('--dataset',choices=DATASETS);p.add_argument('--backend',choices=BACKENDS);a=p.parse_args()
    if a.action=='train':train(a.state,a.dataset,a.backend)
    else:globals()[a.action](a.state)
