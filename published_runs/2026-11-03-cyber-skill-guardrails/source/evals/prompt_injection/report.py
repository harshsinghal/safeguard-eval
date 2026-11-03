"""Reproduce frozen selections' results without loading raw prompt text."""
import argparse
from collections import defaultdict
import csv
import numpy as np
from .common import *

def intervals(metadata,systems,repetitions=2000):
    """Paired bootstrap of related text groups; suitable for one-class stress sets."""
    names=sorted(systems);groups=sorted({r['group'] for r in metadata});gi={g:i for i,g in enumerate(groups)}
    cube=np.zeros((len(groups),len(names),6),dtype=np.int32)
    for j,name in enumerate(names):
        by={r['id']:r for r in systems[name]}
        for r in metadata:
            p=by[r['id']]['prediction'];y=r['expected']
            code=(0 if p=='BLOCK' else 3 if p=='ALLOW' else 5) if y=='BLOCK' else (1 if p=='ALLOW' else 2 if p=='BLOCK' else 4)
            cube[gi[r['group']],j,code]+=1
    rng=np.random.default_rng(20261102);samples=defaultdict(list)
    binary=len({r['expected'] for r in metadata})==2
    for start in range(0,repetitions,32):
        c=cube[rng.integers(0,len(groups),(min(32,repetitions-start),len(groups)))].sum(axis=1).astype(float)
        tp,tn,fp,fn,ea,eb=[c[:,:,k] for k in range(6)];pos=tp+fn+eb;neg=tn+fp+ea
        div=lambda a,b:np.divide(a,b,out=np.full_like(a,np.nan),where=b>0)
        d={'accuracy':div(tp+tn,pos+neg),'attack_recall':div(tp,pos),'benign_allow_rate':div(tn,neg),
            'false_block_rate':div(fp,neg),'missed_attack_rate':div(fn,pos)}
        if binary:d['balanced_accuracy']=(d['attack_recall']+d['benign_allow_rate'])/2
        for k,v in d.items():samples[k].append(v)
    samples={k:np.concatenate(v) for k,v in samples.items()}
    def ci(v):
        v=v[np.isfinite(v)]
        return np.quantile(v,[.025,.975]).tolist() if len(v) else None
    result={name:{k:ci(v[:,j]) for k,v in samples.items()} for j,name in enumerate(names)}
    differences={}
    for slug in MODELS:
        a,b=names.index(slug+'/brief'),names.index(slug+'/selected')
        differences[slug]={k:ci(v[:,b]-v[:,a]) for k,v in samples.items()}
    return dict(repetitions=repetitions,seed=20261102,groups=len(groups),intervals=result,
        selected_minus_brief=differences,method='paired percentile bootstrap of connected text groups; no multiple-comparison adjustment')

def summarize(state,out):
    state=Path(state);out=Path(out);verify(state,test=True)
    freeze=read(state/'freeze.json');metadata=rows(state/'metadata/test.jsonl');systems={}
    for slug in MODELS:
        for arm,pid in [('brief','brief'),('selected',freeze['selected'][slug])]:
            systems[slug+'/'+arm]=completed(state,slug,'test',pid)
    result={'created_utc':now(),'selected':freeze['selected'],'datasets':{},'slices':{}}
    table=[]
    for ds in sorted({r['dataset'] for r in metadata}):
        mm=[r for r in metadata if r['dataset']==ds]
        ss={k:[r for r in v if r['dataset']==ds] for k,v in systems.items()}
        result['datasets'][ds]={'metrics':{k:measures(v) for k,v in ss.items()},'uncertainty':intervals(mm,ss)}
        for name,rr in ss.items():
            m=measures(rr);table.append({'dataset':ds,'system':name,**{k:m[k] for k in (
                'n','accuracy','balanced_accuracy','macro_f1','mcc','recall','specificity','false_blocks','missed_violations','unresolved','coverage')}})
        slices={}
        for field in ('attack_method','trigger_group','category'):
            for value in sorted({r[field] for r in mm if field in r}):
                slices[field+'='+value]={name:measures([r for r in rr if r.get(field)==value]) for name,rr in ss.items()}
        for field in ('non_ascii','format_characters','punctuation_run','long_message'):
            for value in (False,True):
                if any(r['slices'][field]==value for r in mm):
                    slices[field+'='+str(value)]={name:measures([r for r in rr if r['slices'][field]==value]) for name,rr in ss.items()}
        result['slices'][ds]=slices
    write(out/'summary.json',result)
    with (out/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    print(canonical({'output':str(out),'rows':len(table),'complete_test_examples':len(metadata),'selected':freeze['selected']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    summarize(**vars(p.parse_args()))
