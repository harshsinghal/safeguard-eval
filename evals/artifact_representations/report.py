"""Reproduce aggregate results from metadata and recorded predictions."""
import argparse
from collections import defaultdict
import numpy as np
from .common import *

def intervals(rr, base=None):
    groups=defaultdict(list)
    for r in rr: groups[r['group']].append(r)
    old={r['id']:r for r in base} if base else None
    def contribution(x):
        return [sum(r['expected']=='BLOCK' for r in x),sum(r['expected']=='ALLOW' for r in x),
            sum(r['expected']=='BLOCK' and r['prediction']=='BLOCK' for r in x),
            sum(r['expected']=='ALLOW' and r['prediction']=='ALLOW' for r in x)]
    mat=np.array([contribution(x) for x in groups.values()]);ref=np.array([contribution([old[r['id']] for r in x]) for x in groups.values()]) if old else None
    rng=np.random.default_rng(SEEDS[0]);values=[];diff=[]
    for _ in range(2000):
        ix=rng.integers(0,len(mat),len(mat));p,n,tp,tn=mat[ix].sum(0)
        if not p or not n: continue
        ba=.5*(tp/p+tn/n);values.append(ba)
        if ref is not None:
            p0,n0,tp0,tn0=ref[ix].sum(0);diff.append(ba-.5*(tp0/p0+tn0/n0))
    return dict(balanced_accuracy_ci95=np.quantile(values,[.025,.975]).tolist(),
        delta_ci95=np.quantile(diff,[.025,.975]).tolist() if diff else None,groups=len(mat))

def report(state, prior, public=False):
    state=Path(state);prior=Path(prior)
    if not public: verify(state,test=True)
    freeze=read(state/'freeze.json');oldfreeze=read(prior/'freeze.json');result={}
    for task in TASKS:
        result[task]={}
        old={}
        for slug in ('qwen','liquid','tfidf'):
            old[slug]=rows(prior/f'predictions/{slug}/{task}/test/{oldfreeze["selected"][task][slug]}.jsonl')
        for slug,best in freeze['selected'][task].items():
            pids=[f'{best}-s{s}' for s in SEEDS] if slug.endswith('-mlp') else [best]
            rr=complete(state,slug,task,'test',pids[0]);m=measures(rr)
            base=complete(state,slug,task,'test','brief') if slug.startswith('qwen') else None
            result[task][slug]=dict(selected=best,metrics=m,**intervals(rr,base),
                baseline=measures(base) if base else None,
                seeds={str(seed):measures(complete(state,slug,task,'test',pid)) for seed,pid in zip(SEEDS,pids)} if len(pids)>1 else None,
                comparison={name:dict(delta_balanced_accuracy=m['balanced_accuracy']-measures(ref)['balanced_accuracy'],**intervals(rr,ref)) for name,ref in old.items()},
                slices={field:{str(value):measures([r for r in rr if r.get(field)==value]) for value in sorted({r.get(field) for r in rr},key=str)} for field in ('source','clipped')})
    write(state/'results.json',dict(freeze_sha256=digest(state/'freeze.json'),tasks=result))
    print(canonical({task:{slug:r['metrics'] for slug,r in models.items()} for task,models in result.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--prior',required=True);p.add_argument('--public',action='store_true')
    a=p.parse_args();report(a.state,a.prior,a.public)
