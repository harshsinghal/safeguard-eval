"""Fit compact heads, using fitting labels only; select on validation."""
import argparse
import copy
import time
import numpy as np
from .common import *

def features(state, slug, task, split):
    rr=data(state,task,split)
    with np.load(Path(state)/f'features/{slug}/{task}/{split}.npz',allow_pickle=False) as f:
        if f['ids'].tolist()!=[r['id'] for r in rr]: raise ValueError('Feature ID/order mismatch')
        x=f['x'].copy()
    if not np.isfinite(x).all(): raise ValueError('Nonfinite features')
    return rr,x

def emit(state, slug, task, split, pid, rr, scores):
    pred=predictions(rr,scores,slug,pid)
    jsonl(Path(state)/f'predictions/{slug}/{task}/{split}/{pid}.jsonl',pred)
    return measures(pred)

def train(state, embedding):
    import joblib
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    state=Path(state);verify(state);start=time.monotonic()
    for task in TASKS:
        fit,xf=features(state,embedding,task,'fit');val,xv=features(state,embedding,task,'validation')
        y=np.array([r['expected']=='BLOCK' for r in fit],dtype=np.int64)
        if y.sum()*2!=len(y): raise ValueError('Expected balanced fitting data')
        scaler=StandardScaler().fit(xf);xf=scaler.transform(xf);xv=scaler.transform(xv)
        for kind in ('lr','mlp'):
            slug=embedding+'-'+kind;folder=state/f'learned/{slug}/{task}';folder.mkdir(parents=True,exist_ok=True)
            summary={};configs={};models={}
            if kind=='lr':
                for c in (.1,1.,10.):
                    pid=f'C{c:g}';m=LogisticRegression(C=c,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=SEEDS[0]).fit(xf,y)
                    summary[pid]=emit(state,slug,task,'validation',pid,val,m.predict_proba(xv)[:,1]);models[pid]=m;configs[pid]={'C':c}
                best=min(summary,key=lambda p:(-summary[p]['balanced_accuracy'],-summary[p]['macro_f1'],configs[p]['C']))
                chosen={best:models[best]}
            else:
                for hidden in (128,256):
                    for alpha in (.0001,.01):
                        for seed in SEEDS:
                            m=MLPClassifier(hidden_layer_sizes=(hidden,),activation='relu',solver='adam',alpha=alpha,
                                batch_size=64,learning_rate_init=.001,max_iter=1,shuffle=True,random_state=seed,
                                early_stopping=False,learning_rate='constant')
                            for epoch in range(1,61):
                                m.partial_fit(xf,y,classes=np.array([0,1]))
                                if epoch not in (10,30,60): continue
                                base=f'h{hidden}-a{alpha:g}-e{epoch}';pid=f'{base}-s{seed}'
                                summary[pid]=emit(state,slug,task,'validation',pid,val,m.predict_proba(xv)[:,1])
                                configs[base]=dict(hidden=hidden,alpha=alpha,epoch=epoch)
                                models[pid]=copy.deepcopy(m)
                aggregate={p:{key:float(np.mean([summary[f'{p}-s{s}'][key] for s in SEEDS])) for key in ('balanced_accuracy','macro_f1')} for p in configs}
                best=min(configs,key=lambda p:(-aggregate[p]['balanced_accuracy'],-aggregate[p]['macro_f1'],configs[p]['hidden'],configs[p]['epoch'],-configs[p]['alpha']))
                chosen={f'{best}-s{s}':models[f'{best}-s{s}'] for s in SEEDS}
            evidence={}
            for pid,m in chosen.items():
                dest=folder/(pid+'.joblib');joblib.dump({'scaler':scaler,'classifier':m},dest,compress=3)
                restored=joblib.load(dest)
                if not np.array_equal(restored['classifier'].predict_proba(xv),m.predict_proba(xv)): raise ValueError('Checkpoint reload drift')
                evidence[str(dest.relative_to(state))]=digest(dest)
            for p in (state/f'predictions/{slug}/{task}/validation').glob('*.jsonl'): evidence[str(p.relative_to(state))]=digest(p)
            for part in ('fit','validation'):
                p=state/f'features/{embedding}/{task}/{part}.npz';evidence[str(p.relative_to(state))]=digest(p)
            write(folder/'selection.json',dict(selected=best,validation=summary,configs=configs,
                aggregate=aggregate if kind=='mlp' else None,evidence=evidence,seeds=list(SEEDS) if kind=='mlp' else [SEEDS[0]]))
            print(canonical(dict(model=slug,task=task,selected=best)),flush=True)
            del models,chosen
    write(state/f'runtime/{embedding}-heads.json',dict(created_utc=now(),seconds=time.monotonic()-start))

def test(state, embedding):
    import joblib
    state=Path(state);verify(state,test=True);freeze=read(state/'freeze.json')
    for task in TASKS:
        rr,x=features(state,embedding,task,'test')
        val,xv=features(state,embedding,task,'validation')
        for kind in ('lr','mlp'):
            slug=embedding+'-'+kind;best=freeze['selected'][task][slug]
            for pid in ([best] if kind=='lr' else [f'{best}-s{s}' for s in SEEDS]):
                m=joblib.load(state/f'learned/{slug}/{task}/{pid}.joblib')
                scores=m['classifier'].predict_proba(m['scaler'].transform(xv))[:,1]
                old={r['id']:r for r in complete(state,slug,task,'validation',pid)}
                if max(abs(float(s)-old[r['id']]['score']) for s,r in zip(scores,val))>1e-7: raise ValueError('Validation checkpoint mismatch')
                emit(state,slug,task,'test',pid,rr,m['classifier'].predict_proba(m['scaler'].transform(x))[:,1])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--slug',choices=['jina-v2','jina-code'],required=True)
    p.add_argument('--split',choices=['validation','test'],required=True);a=p.parse_args()
    (train if a.split=='validation' else test)(a.state,a.slug)
