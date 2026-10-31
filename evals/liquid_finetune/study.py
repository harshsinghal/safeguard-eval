"""CPU selection, immutable pretest freeze, and final labeled evaluation."""
import argparse
import warnings
import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from .common import *
from evals.leaderboard.metrics import metrics, THRESHOLDS


def select(y,candidates):
    best={p:None for p in PROFILES};grid=[]
    for cid,c in sorted(candidates.items()):
        for t in THRESHOLDS:
            mm=[metrics(y,np.asarray(s)>=t) for s in c['scores']]
            avg={k:float(np.mean([m[k] for m in mm])) for k in
                ['accuracy','balanced_accuracy','recall','specificity','macro_f1','false_positive_rate']}
            tail=(-float(np.mean([min(m['recall'],m['specificity']) for m in mm])),
                  -avg['macro_f1'],abs(t-.5),t,cid)
            row=dict(candidate=cid,threshold=t,mean_validation=avg,seed_validation=mm)
            grid.append(dict(candidate=cid,threshold=t,**avg))
            for profile in PROFILES:
                if profile=='false_block_limit' and any(m['false_positive_rate']>.05+1e-12 for m in mm):continue
                if profile=='catch_target' and any(m['recall']<.90-1e-12 for m in mm):continue
                first={'accuracy':(-avg['accuracy'],),'balanced':(-avg['balanced_accuracy'],),
                       'false_block_limit':(-avg['recall'],avg['false_positive_rate']),
                       'catch_target':(avg['false_positive_rate'],-avg['recall'])}[profile]
                key=first+tail
                if best[profile] is None or key<best[profile]['rank_key']:
                    best[profile]=dict(**row,rank_key=key)
    return best,grid


def prepare_selection(state):
    state=Path(state);check_registration(state)
    if (state/'freeze.json').exists():raise ValueError('Already frozen')
    features={};metas={}
    for split in ['fit','validation']:
        folder=state/'features'/split;m=read(folder/'manifest.json')
        if digest(folder/'features.npy')!=m['features_sha256']:raise ValueError('Changed features')
        metas[split]=aligned_metadata(state,split,m['ids'])
        features[split]=np.load(folder/'features.npy',allow_pickle=False)
        if features[split].shape!=(len(metas[split]),1024) or not np.isfinite(features[split]).all():
            raise ValueError('Invalid or missing features')
    y,yv=labels(metas['fit']),labels(metas['validation'])
    scaler=StandardScaler().fit(features['fit'])
    # Use exactly the same float64 arithmetic and final cast during inference.
    x=((features['fit']-scaler.mean_)/scaler.scale_).astype(np.float32)
    xv=((features['validation']-scaler.mean_)/scaler.scale_).astype(np.float32)
    folder=state/'fits/frozen';folder.mkdir(parents=True,exist_ok=False)
    np.savez(folder/'scaler.npz',mean=scaler.mean_,scale=scaler.scale_)
    candidates={};failed=[]
    for c in CS:
        cid=f'frozen-c{c:g}'
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning)
            try:clf=LogisticRegression(C=c,class_weight=None,solver='lbfgs',max_iter=3000,tol=1e-6).fit(x,y)
            except ConvergenceWarning:
                failed.append(cid);continue
        path=folder/(cid+'.npz');np.savez(path,coef=clf.coef_[0],intercept=clf.intercept_[0])
        score=expit(xv@clf.coef_[0]+clf.intercept_[0])
        candidates[cid]=dict(kind='frozen',C=c,seeds=[SEEDS[0]],scores=[score.tolist()],
                            parameters=[str(path.relative_to(state))],iterations=int(clf.n_iter_[0]))
    for rate in RATES:
        for seed in SEEDS:
            h=read(state/'fits'/f'ft-lr{rate:g}-s{seed}'/'history.json')
            if h['rate']!=rate or h['seed']!=seed or [r['epoch'] for r in h['epochs']]!=[1,2,3]:
                raise ValueError('Incomplete training search')
            if h['validation_tokenization']['ids']!=[r['id'] for r in metas['validation']]:
                raise ValueError('Validation ordering changed')
            for r in h['epochs']:
                cid=f'finetuned-lr{rate:g}-e{r["epoch"]}'
                can=candidates.setdefault(cid,dict(kind='finetuned',rate=rate,epoch=r['epoch'],seeds=[],scores=[],parameters=[],parameter_hashes=[]))
                can['seeds'].append(seed);can['scores'].append(r['validation_scores'])
                can['parameters'].append(r['checkpoint']);can['parameter_hashes'].append(r['checkpoint_sha256'])
    for c in candidates.values():
        if len(c['scores'])!=len(c['seeds']) or any(len(s)!=len(yv) or not np.isfinite(s).all() for s in c['scores']):
            raise ValueError('Candidate coverage mismatch')
    choices={};grids={}
    for kind in ['frozen','finetuned']:
        choices[kind],grids[kind]=select(yv,{k:c for k,c in candidates.items() if c['kind']==kind})
    write(state/'validation.json',dict(metadata=metas['validation'],candidates=candidates,
        choices=choices,grids=grids,failed_frozen_candidates=failed),exclusive=True)
    print('SELECTED',{k:{p:(r['candidate'],r['threshold'],r['mean_validation']['accuracy']) for p,r in cc.items()} for k,cc in choices.items()},flush=True)


def freeze(state):
    state=Path(state);check_registration(state);v=read(state/'validation.json')
    hashes={'validation.json':digest(state/'validation.json')};checkpoints={}
    for p in (state/'fits').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.npz']:hashes[str(p.relative_to(state))]=digest(p)
    for p in (state/'features').rglob('manifest.json'):hashes[str(p.relative_to(state))]=digest(p)
    for c in v['choices']['finetuned'].values():
        can=v['candidates'][c['candidate']]
        for p,h in zip(can['parameters'],can['parameter_hashes']):checkpoints[p]=h
    write(state/'freeze.json',dict(created_utc=now(),sources=sources(),hashes=hashes,
        selected_checkpoints=checkpoints,choices=v['choices'],registration_sha256=digest(state/'registration.json'),
        primary_profile='accuracy',primary_seed=SEEDS[0],test_data_uploaded=False,
        note='Selection uses validation only; the public test was examined in prior studies.'),exclusive=True)
    print('FROZEN',len(checkpoints),'selected fine-tuned checkpoint files',flush=True)


def score(y,s,threshold):
    s=np.asarray(s,dtype=float)
    if s.shape!=y.shape or not np.isfinite(s).all() or (s<0).any() or (s>1).any():
        raise ValueError('Invalid score or dropped examples')
    m=metrics(y,(s>=threshold).astype(int),s);ss=np.clip(s,1e-7,1-1e-7)
    m.update(brier=float(np.mean((s-y)**2)),log_loss=float(-np.mean(y*np.log(ss)+(1-y)*np.log(1-ss))))
    return m


def paired_intervals(meta,a,b,repetitions=2000):
    """Paired duplicate-group resampling, including ordinary accuracy."""
    y=labels(meta);groups=sorted({r['group'] for r in meta});gi={g:i for i,g in enumerate(groups)}
    cube=np.zeros((len(groups),2,4),dtype=np.int32)
    for j,pred in enumerate([a,b]):
        for i,p in enumerate(pred):
            col=(0 if p else 3) if y[i] else (2 if p else 1)
            cube[gi[meta[i]['group']],j,col]+=1
    vals={m:[] for m in ['accuracy','balanced_accuracy','recall','specificity']}
    rng=np.random.default_rng(20261031)
    for start in range(0,repetitions,32):
        draws=rng.integers(0,len(groups),size=(min(32,repetitions-start),len(groups)))
        c=cube[draws].sum(1);tp,tn,fp,fn=[c[:,:,i].astype(float) for i in range(4)]
        recall=tp/(tp+fn);specificity=tn/(tn+fp)
        for m,z in dict(accuracy=(tp+tn)/(tp+tn+fp+fn),balanced_accuracy=(recall+specificity)/2,
                        recall=recall,specificity=specificity).items():
            vals[m].extend((z[:,0]-z[:,1]).tolist())
    return {k:np.quantile(v,[.025,.975]).tolist() for k,v in vals.items()}


def summarize(meta,predictions):
    y=labels(meta);profiles={};contrasts={};slices={}
    for profile in PROFILES:
        profiles[profile]={}
        for kind in ['frozen','finetuned']:
            r=predictions[kind][profile];mm=[score(y,s,r['threshold']) for s in r['scores']]
            fixed=[score(y,s,.5) for s in r['scores']]
            profiles[profile][kind]=dict(candidate=r['candidate'],threshold=r['threshold'],seeds=r['seeds'],
                seed_metrics=mm,fixed_half_metrics=fixed,
                summary={k:dict(mean=float(np.mean([m[k] for m in mm])),min=float(min(m[k] for m in mm)),max=float(max(m[k] for m in mm)))
                         for k in ['accuracy','balanced_accuracy','false_blocks','missed_violations']})
        if profile in ['accuracy','balanced']:
            ra,rb=[predictions[k][profile] for k in ['finetuned','frozen']]
            a=np.asarray(ra['scores'][0])>=ra['threshold'];b=np.asarray(rb['scores'][0])>=rb['threshold']
            ma,mb=[profiles[profile][k]['seed_metrics'][0] for k in ['finetuned','frozen']]
            contrasts[profile]=dict(accuracy_delta=ma['accuracy']-mb['accuracy'],
                balanced_accuracy_delta=ma['balanced_accuracy']-mb['balanced_accuracy'],
                ci95=paired_intervals(meta,a,b),corrected=int(((a==y)&(b!=y)).sum()),
                newly_wrong=int(((a!=y)&(b==y)).sum()),
                false_blocks_delta=ma['false_blocks']-mb['false_blocks'],misses_delta=ma['missed_violations']-mb['missed_violations'])
    for field in ['subcategory','adversarial']:
        slices[field]={}
        for value in sorted({str(r.get(field)) for r in meta}):
            mask=np.asarray([str(r.get(field))==value for r in meta]);slices[field][value]={}
            for kind in ['frozen','finetuned']:
                r=predictions[kind]['accuracy'];s=np.asarray(r['scores'][0])[mask]
                slices[field][value][kind]=score(y[mask],s,r['threshold'])
    return dict(profiles=profiles,paired_contrasts=contrasts,slices=slices)


def evaluate(state):
    state=Path(state);f=check_freeze(state);check_registration(state,test=True)
    if (state/'results.json').exists():raise ValueError('Immutable test result exists')
    v=read(state/'validation.json');out=read(state/'test-output/scores.json')
    meta=aligned_metadata(state,'test',out['tokenization']['ids'])
    if out['tokenization']['input_sha256']!=digest(state/'inputs/test.jsonl'):
        raise ValueError('Test text changed')
    path=state/'test-output/frozen-features.npy'
    if digest(path)!=out['frozen_feature_sha256']:raise ValueError('Test features changed')
    raw=np.load(path,allow_pickle=False);sc=np.load(state/'fits/frozen/scaler.npz',allow_pickle=False)
    if raw.shape!=(len(meta),1024) or not np.isfinite(raw).all():raise ValueError('Invalid test features')
    x=((raw-sc['mean'])/sc['scale']).astype(np.float32)
    predictions={}
    for kind,choices in f['choices'].items():
        predictions[kind]={}
        for profile,c in choices.items():
            can=v['candidates'][c['candidate']];ss=[]
            for p in can['parameters']:
                if kind=='frozen':
                    par=np.load(state/p,allow_pickle=False);ss.append(expit(x@par['coef']+par['intercept']).tolist())
                else:
                    record=out['checkpoints'][p]
                    if record['sha256']!=f['selected_checkpoints'][p]:raise ValueError('Checkpoint hash mismatch')
                    ss.append(record['scores'])
            predictions[kind][profile]=dict(candidate=c['candidate'],threshold=c['threshold'],scores=ss,seeds=can['seeds'])
    write(state/'test-predictions.json',dict(metadata=meta,predictions=predictions),exclusive=True)
    result=summarize(meta,predictions)
    write(state/'results.json',dict(created_utc=now(),freeze_sha256=digest(state/'freeze.json'),**result),exclusive=True)
    for profile in ['accuracy','balanced']:
        for kind,rec in result['profiles'][profile].items():
            m=rec['seed_metrics'][0];print(profile,kind,'accuracy',m['accuracy'],'BA',m['balanced_accuracy'],
                                         'FP',m['false_blocks'],'FN',m['missed_violations'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare_selection','freeze','evaluate']);p.add_argument('--state',required=True)
    a=p.parse_args();globals()[a.action](a.state)
