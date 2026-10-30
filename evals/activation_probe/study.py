"""Train-only linear probes, validation selection, pre-test freeze and reporting."""
import argparse
from itertools import combinations
from pathlib import Path
import warnings
import numpy as np
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from .common import (ROOT, CS, PRIMARY, MODELS, keys, labels, load_features, matrix,
                     read, rows, write, digest, now, source_hashes)
from evals.leaderboard.metrics import select, decisions, metrics, bootstrap


def fit_linear(x, y, c):
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    clf = LogisticRegression(C=c,solver='lbfgs',penalty='l2',max_iter=3000,
                             tol=1e-6,random_state=20261030)
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        with threadpool_limits(limits=2):
            clf.fit(z,y)
    return dict(mean=scaler.mean_,scale=scaler.scale_,coef=clf.coef_[0],
                intercept=np.asarray(clf.intercept_[0])),int(clf.n_iter_[0])


def predict(params, x):
    return expit(((x-params['mean'])/params['scale'])@params['coef']+float(params['intercept']))


def candidate(scores, valid):
    return dict(score=[float(s) if v else None for s,v in zip(scores,valid)],
                prediction=np.where(valid,np.asarray(scores)>=.5,-1).astype(int).tolist())


def all_features(state, split):
    features={}; validity={}; manifests={}; meta=None
    for model in MODELS:
        mm, ff, vv, manifest = load_features(state,model,split)
        if meta is not None and meta!=mm:
            raise ValueError('Encoder populations do not align')
        meta=mm;features.update(ff);validity[model]=vv;manifests[model]=manifest
    return meta, features, validity, manifests


def validity_for(validity, representation):
    return np.logical_and.reduce([validity[k.split('-')[0]] for k in representation])


def train(state):
    state=Path(state)
    if (state/'freeze.json').exists():
        raise ValueError('Study already frozen')
    fitmeta,xf,vf,_=all_features(state,'fit')
    valmeta,xv,vv,_=all_features(state,'validation')
    yf,yv=labels(fitmeta),labels(valmeta)
    spec={}; outputs={}; chosen={}; grids={}; invalid=[]
    def run(representation):
        prefix='+'.join(representation)
        xtrain,xval=matrix(xf,representation),matrix(xv,representation)
        fitvalid=validity_for(vf,representation);valvalid=validity_for(vv,representation)
        ids=[]
        for c in CS:
            cid=prefix+f'__C{c:g}'
            if cid not in outputs:
                try:
                    params,iters=fit_linear(xtrain[fitvalid],yf[fitvalid],c)
                except ConvergenceWarning:
                    invalid.append(dict(id=cid,reason='ConvergenceWarning'));continue
                file=state/'fits'/(cid+'.npz');file.parent.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(file,**params)
                spec[cid]=dict(representation=representation,C=c,fit_rows=int(fitvalid.sum()),
                               iterations=iters,path=str(file.relative_to(state)),sha256=digest(file))
                score=np.full(len(yv),np.nan);score[valvalid]=predict(params,xval[valvalid])
                outputs[cid]=candidate(score,valvalid)
                print('FIT',cid,'iterations',iters,flush=True)
            ids.append(cid)
        if not ids:raise ValueError('No converged candidates')
        return ids
    for model in MODELS:
        ids=run([PRIMARY[model]])
        chosen['primary-'+model],grids['primary-'+model]=select(yv,{i:outputs[i] for i in ids})
    ids=run([PRIMARY['qwen'],PRIMARY['policylm']])
    chosen['primary-combined'],grids['primary-combined']=select(yv,{i:outputs[i] for i in ids})
    secondary_reps=[]
    for model in MODELS:
        ids=[]
        for key in keys(model):ids+=run([key])
        chosen['secondary-'+model],grids['secondary-'+model]=select(yv,{i:outputs[i] for i in ids})
        selected=chosen['secondary-'+model]['balanced']['candidate']
        secondary_reps+=spec[selected]['representation']
    ids=run(secondary_reps)
    chosen['secondary-combined'],grids['secondary-combined']=select(yv,{i:outputs[i] for i in ids})
    records=read(state/'features/policylm/validation/records.json')
    if [r['id'] for r in records]!=[r['id'] for r in valmeta]:raise ValueError('Native score order')
    native=np.asarray([r['native_score'] for r in records])
    outputs['policylm-native']=candidate(native,vv['policylm'])
    chosen['policylm-native'],grids['policylm-native']=select(yv,{'policylm-native':outputs['policylm-native']})
    stronger=min(('primary-qwen','primary-policylm'),
        key=lambda g:(-chosen[g]['balanced']['metrics']['balanced_accuracy'],g))
    write(state/'validation.json',dict(metadata=valmeta,candidates=outputs,choices=chosen,grids=grids))
    write(state/'fits.json',spec)
    artifacts={str(p.relative_to(state)):digest(p) for p in sorted((state/'fits').glob('*.npz'))}
    artifacts.update({n:digest(state/n) for n in ['validation.json','fits.json','policy.json']})
    feature_hashes={str(p.relative_to(state)):digest(p)
                    for model in MODELS for split in ('fit','validation')
                    for p in sorted((state/'features'/model/split).iterdir()) if p.is_file()}
    freeze=dict(created_utc=now(),sources=source_hashes(),data_manifest_sha256=digest(state/'data-manifest.json'),
                artifacts=artifacts,development_feature_hashes=feature_hashes,choices=chosen,
                primary_stronger_single=stronger,invalid_candidates=invalid,probe_fits=len(spec),
                secondary_combined_representations=secondary_reps,
                note='Test labels, outputs and features were not inputs to fitting or selection.')
    write(state/'freeze.json',freeze,exclusive=True)
    print('FROZEN',len(spec),'fits; stronger single:',stronger,flush=True)


def check_freeze(state, include_features=False):
    f=read(state/'freeze.json')
    if f['sources']!=source_hashes() or f['data_manifest_sha256']!=digest(state/'data-manifest.json'):
        raise ValueError('Frozen code or data manifest changed')
    expected=dict(f['artifacts'])
    if include_features:expected.update(f['development_feature_hashes'])
    for relative,h in expected.items():
        if digest(state/relative)!=h:raise ValueError('Frozen artifact changed: '+relative)
    return f


def score_metrics(y,p,s):
    m=metrics(y,p,s)
    if np.isfinite(s).all() and (p!=-1).all():
        ss=np.clip(s,1e-7,1-1e-7)
        m.update(brier=float(np.mean((ss-y)**2)),log_loss=float(-np.mean(y*np.log(ss)+(1-y)*np.log(1-ss))))
    return m


def historical_controls(meta):
    import gzip,json
    folder=ROOT/'published_runs/2026-10-30-leaderboard-decision-ensembles'
    selection=read(folder/'selection.json')['wildguard']
    with gzip.open(folder/'test/wildguard.json.gz','rt') as f:raw=json.load(f)
    index={r['id']:i for i,r in enumerate(raw['metadata'])}
    order=[index[r['id']] for r in meta]
    for r,i in zip(meta,order):
        if any(r[k]!=raw['metadata'][i][k] for k in ('expected','group','prompt_sha256')):
            raise ValueError('Historical test alignment')
    out={}
    # Exact family keys are found by identity, not by observed test performance.
    for group,label in [('wildguard','historical-wildguard'),
                        ('wildguard-specialists/logit-equal','historical-specialist-equal-logodds')]:
        if group not in selection:raise ValueError('Historical control missing')
        c=selection[group]['choices']['balanced'];rawc=raw['candidates'][c['candidate']]
        p=decisions(rawc,c['threshold'])[order]
        out[label]=dict(prediction=p.tolist(),score=None,selection=c,validation_population='historical common 512')
    return out


def evaluate(state):
    state=Path(state);f=check_freeze(state)
    if (state/'test-results.json').exists():raise ValueError('Immutable test results exist')
    meta,xx,vv,_=all_features(state,'test');y=labels(meta)
    specs=read(state/'fits.json');outputs={};profiles={};predictions={}
    needed={c['candidate'] for choices in f['choices'].values() for c in choices.values() if c}
    for cid in sorted(needed):
        if cid=='policylm-native':
            records=read(state/'features/policylm/test/records.json')
            if [r['id'] for r in records]!=[r['id'] for r in meta]:raise ValueError('Native score order')
            s=np.asarray([r['native_score'] for r in records]);valid=vv['policylm']
        else:
            spec=specs[cid];valid=validity_for(vv,spec['representation'])
            s=np.full(len(y),np.nan)
            with np.load(state/spec['path'],allow_pickle=False) as p:
                s[valid]=predict(p,matrix(xx,spec['representation'])[valid])
        outputs[cid]=candidate(s,valid)
    for profile in ('balanced','false_block_limit','catch_target'):
        result={}
        for group,choices in f['choices'].items():
            c=choices[profile]
            if c is None:
                result[group]=None;continue
            cand=outputs[c['candidate']];p=decisions(cand,c['threshold'])
            s=np.asarray([np.nan if v is None else v for v in cand['score']])
            result[group]=dict(candidate=c['candidate'],threshold=c['threshold'],
                               validation=c['metrics'],test=score_metrics(y,p,s))
            if profile=='balanced':predictions[group]=p
        profiles[profile]=result
    npred=decisions(outputs['policylm-native'],.5);predictions['policylm-native-0.5']=npred
    profiles['balanced']['policylm-native-0.5']=dict(candidate='policylm-native',threshold=.5,
        validation=None,test=metrics(y,npred,outputs['policylm-native']['score']))
    hist=historical_controls(meta)
    for group,r in hist.items():
        p=np.asarray(r['prediction']);predictions[group]=p
        profiles['balanced'][group]=dict(candidate=r['selection']['candidate'],
            threshold=r['selection']['threshold'],validation=r['selection']['metrics'],
            test=metrics(y,p),caveat=r['validation_population'])
    boot=bootstrap(meta,predictions)
    intervals={g:{k:[float(v) for v in np.nanquantile(a,[.025,.975])] for k,a in mm.items()}
               for g,mm in boot.items()}
    pairs=[]
    for g in ('primary-combined','secondary-combined'):
        for other in predictions:
            if other==g:continue
            d=boot[g]['balanced_accuracy']-boot[other]['balanced_accuracy']
            pairs.append(dict(method=g,comparator=other,
                balanced_accuracy_delta=profiles['balanced'][g]['test']['balanced_accuracy']-profiles['balanced'][other]['test']['balanced_accuracy'],
                ci95=[float(v) for v in np.quantile(d,[.025,.975])],
                corrected=int(((predictions[g]==y)&(predictions[other]!=y)).sum()),
                newly_wrong=int(((predictions[g]!=y)&(predictions[other]==y)).sum())))
    slices={}
    for field in ('subcategory','adversarial'):
        slices[field]={}
        for value in sorted({str(r.get(field)) for r in meta}):
            mask=np.asarray([str(r.get(field))==value for r in meta])
            slices[field][value]={g:metrics(y[mask],p[mask]) for g,p in predictions.items()}
    write(state/'test-predictions.json',dict(metadata=meta,candidates=outputs,
                                           balanced_predictions={g:p.tolist() for g,p in predictions.items()}))
    result=dict(created_utc=now(),freeze_sha256=digest(state/'freeze.json'),profiles=profiles,
                ci95=intervals,paired_differences=pairs,slices=slices,
                bootstrap_repetitions=2000,primary_stronger_single=f['primary_stronger_single'],
                extraction={model:{split:read(state/'features'/model/split/'manifest.json')
                                       for split in ('fit','validation','test')} for model in MODELS})
    write(state/'test-results.json',result,exclusive=True)
    for g,r in profiles['balanced'].items():
        m=r['test'];print(g,round(m['balanced_accuracy']*100,3),'FP',m['false_blocks'],'FN',m['missed_violations'],flush=True)


def reproduce(state, refit=False):
    state=Path(state);f=check_freeze(state,include_features=refit)
    saved=read(state/'test-predictions.json');y=labels(saved['metadata']);result=read(state/'test-results.json')
    for g,p in saved['balanced_predictions'].items():
        got=metrics(y,p)
        for key,value in got.items():
            if value!=result['profiles']['balanced'][g]['test'][key]:raise ValueError('Metric reproduction failed')
    if refit:
        meta,xf,vf,_=all_features(state,'fit');val,xv,vv,_=all_features(state,'validation')
        fitlabels=labels(meta);outputs=read(state/'validation.json')['candidates'];specs=read(state/'fits.json')
        for cid,spec in specs.items():
            reps=spec['representation'];valid=validity_for(vf,reps);vvalid=validity_for(vv,reps)
            params,_=fit_linear(matrix(xf,reps)[valid],fitlabels[valid],spec['C'])
            scores=predict(params,matrix(xv,reps)[vvalid])
            original=np.asarray(outputs[cid]['score'])[vvalid]
            if not np.allclose(scores,original,atol=1e-9,rtol=1e-9):raise ValueError('Refit reproduction failed: '+cid)
        print('All',len(specs),'fits reproduced',flush=True)
    print('Published balanced metrics reproduced',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','evaluate','reproduce'])
    p.add_argument('--state',required=True);p.add_argument('--refit',action='store_true')
    args=p.parse_args()
    if args.action=='reproduce':reproduce(args.state,args.refit)
    else:globals()[args.action](args.state)
