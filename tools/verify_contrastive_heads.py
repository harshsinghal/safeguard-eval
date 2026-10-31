"""Recompute published metrics; optionally reproduce every private candidate fit."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.contrastive_heads.common import *
from evals.contrastive_heads.learn import standardize,linear,neural,neural_predict
from evals.contrastive_heads.study import selections,score
from evals.leaderboard.metrics import bootstrap

def verify(state,refit=False,validation_only=False):
    import torch
    state=Path(state);refits=0;maxdiff=0.;validation_checked=0
    for ds in DATASETS:
        for backend in BACKENDS:
            folder=state/'fits'/ds/backend
            if not (folder/'validation.json').exists():
                if validation_only:continue
                raise ValueError('Missing validation artifact')
            v=read(folder/'validation.json');y=labels(v['metadata'])
            for head in ['lr','mlp','contrastive']:
                got,_=selections(y,{k:c for k,c in v['candidates'].items() if c['head']==head})
                # JSON normalizes tuple rank keys.
                if json.loads(json.dumps(got))!=v['choices'][head]:raise ValueError('Validation selection mismatch')
            if refit:
                fm,x,_=load(state,ds,backend,'fit');vm,xv,_=load(state,ds,backend,'validation');yy=labels(fm)
                _,x,xv=standardize(x,xv)
                for cid,c in v['candidates'].items():
                    if c['head']!='lr':continue
                    clf,s=linear(x,yy,xv,c['C']);d=float(np.max(np.abs(s-np.asarray(c['scores'][0]))));maxdiff=max(maxdiff,d)
                    params=np.load(state/c['parameters'][0],allow_pickle=False)
                    if not np.allclose(clf.coef_[0],params['coef'],atol=1e-9,rtol=1e-9) or d>1e-9:raise ValueError('LR refit differs')
                    refits+=1
                for head in ['mlp','contrastive']:
                    for decay in DECAYS:
                        for seed in SEEDS:
                            for epoch,params,s,history in neural(x,yy,xv,decay,seed,head=='contrastive'):
                                cid=f'{head}-wd{decay:g}-e{epoch:02d}';c=v['candidates'][cid];i=c['seeds'].index(seed)
                                original=torch.load(state/c['parameters'][i],weights_only=True,map_location='cpu')
                                if any(not torch.equal(params[k],original[k]) for k in params):raise ValueError('Neural refit differs')
                                d=float(np.max(np.abs(s-np.asarray(c['scores'][i]))));maxdiff=max(maxdiff,d)
                                if d>1e-9:raise ValueError('Neural validation score differs')
                                refits+=1
            validation_checked+=1;print('VERIFIED validation',ds,backend,flush=True)
    pairs=0;metrics_checked=0
    if not validation_only:
        result=read(state/'results.json');pred=read(state/'test-predictions.json')
        for ds,rr in result['results'].items():
            meta=pred[ds]['metadata'];y=labels(meta);primary={}
            for profile,table in rr['profiles'].items():
                for name,row in table.items():
                    if row is None:continue
                    raw=pred[ds][name][profile]
                    for s,p,expected in zip(raw['scores'],raw['predictions'],row['seed_metrics']):
                        p,s=np.asarray(p),np.asarray(s)
                        if not np.array_equal(p,(s>=row['selection']['threshold']).astype(int)):raise ValueError('Cutoff mismatch')
                        got=score(y,p,s)
                        if got!=expected:raise ValueError('Metric mismatch')
                        # Independent confusion/accuracy computation.
                        tn=int(((y==0)&(p==0)).sum());tp=int(((y==1)&(p==1)).sum())
                        if got['accuracy']!=(tn+tp)/len(y) or got['balanced_accuracy']!=(tn/(y==0).sum()+tp/(y==1).sum())/2:raise ValueError('Independent metric mismatch')
                        metrics_checked+=1
                    if profile=='balanced':primary[name]=np.asarray(raw['predictions'][0])
            boot=bootstrap(meta,primary)
            for r in rr['paired_contrasts']:
                delta=boot[r['method']]['balanced_accuracy']-boot[r['comparator']]['balanced_accuracy']
                if not np.array_equal(np.quantile(delta,[.025,.975]),r['ci95']):raise ValueError('Bootstrap mismatch')
                pairs+=1
    output=dict(created_utc=now(),validation_groups=validation_checked,refit_candidates=refits,
        maximum_validation_score_difference=maxdiff,verified_test_metric_rows=metrics_checked,verified_paired_intervals=pairs,
        feature_refitting=refit,validation_only=validation_only)
    write(state/('validation-verification.json' if validation_only else 'verification.json'),output)
    print(json.dumps(output,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--refit',action='store_true');p.add_argument('--validation-only',action='store_true')
    verify(**vars(p.parse_args()))
