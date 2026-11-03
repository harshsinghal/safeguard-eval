"""Reproduce metrics from prompt-free prediction records."""
import argparse
from collections import defaultdict
import numpy as np
from .common import *

def intervals(rr, base=None):
    groups=defaultdict(list)
    for r in rr:groups[r['group']].append(r)
    old={r['id']:r for r in base} if base else None
    if old is not None and set(old)!={r['id'] for r in rr}:raise ValueError('Unpaired comparison')
    def contribution(x):
        return [sum(r['expected']=='BLOCK' for r in x),sum(r['expected']=='ALLOW' for r in x),
            sum(r['expected']=='BLOCK' and r['prediction']=='BLOCK' for r in x),
            sum(r['expected']=='ALLOW' and r['prediction']=='ALLOW' for r in x)]
    mat=np.array([contribution(x) for x in groups.values()])
    ref=np.array([contribution([old[r['id']] for r in x]) for x in groups.values()]) if old is not None else None
    rng=np.random.default_rng(SEED);values=[];diff=[]
    for _ in range(2000):
        ix=rng.integers(0,len(mat),len(mat));p,n,tp,tn=mat[ix].sum(0)
        if not p or not n:continue
        ba=.5*(tp/p+tn/n);values.append(ba)
        if ref is not None:
            p0,n0,tp0,tn0=ref[ix].sum(0);diff.append(ba-.5*(tp0/p0+tn0/n0))
    return dict(balanced_accuracy_ci95=np.quantile(values,[.025,.975]).tolist(),
        delta_ci95=np.quantile(diff,[.025,.975]).tolist() if diff else None,groups=len(mat))

def compare(rr,base):
    return dict(reference_metrics=measures(base),
        delta_balanced_accuracy=measures(rr)['balanced_accuracy']-measures(base)['balanced_accuracy'],
        **intervals(rr,base))

def report(state,public=False):
    state=Path(state)
    if not public:verify(state,test=True)
    freeze=read(state/'freeze.json');result={}
    for task in TASKS:
        table={}
        for slug,best in freeze['selected'][task].items():
            pids=[f'{best}-s{s}' for s in SEEDS] if slug.endswith('-mlp') else [best]
            rr=complete(state,slug,task,'test',pids[0])
            row=dict(selected=best,metrics=measures(rr),**intervals(rr),
                diagnostic_only=slug=='promptguard',input_view='skill_only' if '-md-' in slug else 'package')
            if slug in POLICY_MODELS:
                row['policy_vs_brief']=compare(rr,complete(state,slug,task,'test','brief'))
            if slug in MODELS and task=='skills':
                md=complete(state,slug,task,'test',best+'-md')
                row['full_vs_skill_only']=compare(rr,md)
                md_by_id={r['id']:r for r in md}
                multi=[r for r in rr if r['file_count']>1]
                if {r['expected'] for r in multi}=={'ALLOW','BLOCK'}:
                    row['companion_file_subset']=dict(n=len(multi),**compare(multi,[md_by_id[r['id']] for r in multi]))
                single=[r for r in rr if r['file_count']==1]
                row['single_file_repeat_control']=dict(n=len(single),
                    identical_request_hashes=sum(r['request_sha256']==md_by_id[r['id']]['request_sha256'] for r in single),
                    changed_decisions=sum(r['prediction']!=md_by_id[r['id']]['prediction'] for r in single))
            if slug=='llamaguard':
                default=complete(state,slug,task,'test','default')
                row['custom_vs_default']=compare(rr,default)
            if len(pids)>1:
                row['seeds']={str(seed):measures(complete(state,slug,task,'test',pid)) for seed,pid in zip(SEEDS,pids)}
            row['slices']={}
            for field in ('source','category','behavior'):
                if field not in rr[0]:continue
                row['slices'][field]={str(v):measures([r for r in rr if r[field]==v]) for v in sorted({r[field] for r in rr})}
            row['slices']['input_bytes']={label:measures([r for r in rr if low<=r['input_bytes']<high])
                for label,low,high in [('under_2k',0,2000),('2k_to_8k',2000,8000),('8k_to_20k',8000,20001)]
                if any(low<=r['input_bytes']<high for r in rr)}
            table[slug]=row
        if task=='skills':
            for kind in ('lr','mlp'):
                full='jina-v2-'+kind;md='jina-v2-md-'+kind
                def records(slug):
                    pid=freeze['selected'][task][slug]+(f'-s{SEEDS[0]}' if kind=='mlp' else '')
                    return complete(state,slug,task,'test',pid)
                table[full]['full_vs_separately_trained_skill_only']=compare(records(full),records(md))
        meta_rows=rows(state/f'metadata/{task}/test.jsonl')
        result[task]=dict(models=table,baselines={p:measures([{**r,'prediction':p} for r in meta_rows]) for p in ('ALLOW','BLOCK')})
    write(state/'results.json',dict(freeze_sha256=digest(state/'freeze.json'),tasks=result))
    print(canonical({task:{slug:r['metrics'] for slug,r in x['models'].items()} for task,x in result.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--public',action='store_true');a=p.parse_args();report(a.state,a.public)
