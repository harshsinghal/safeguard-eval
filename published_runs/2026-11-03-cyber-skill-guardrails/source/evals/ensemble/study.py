"""Ingest immutable scores, fit on development, freeze, then evaluate once."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import time
import joblib
import numpy as np

from evals.ensemble.common import (ROOT,WG,HX,WG_RUNS,HX_POLICIES,COHORTS,SEED,read,rows,write,write_rows,
    digest,now,align,assert_disjoint,metrics)
from evals.ensemble.learn import search,predict,classify,validity


def fitting_sources():
    return {str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'evals/ensemble/common.py',ROOT/'evals/ensemble/learn.py']}


def ingest(state):
    state=Path(state);data=read(state/'data-manifest.json');audit=[]
    if (state/'ingestion.json').exists():raise ValueError('Ingestion already recorded')
    for model,pid in HX_POLICIES.items():
        for split in ['canary','fit','validation']:
            folder=state/'new-runs'/model/split;m=read(folder/'manifest.json');completed=read(folder/'completion.json')
            if m['revision']!=data['hx_models'][model]['revision'] or m['policy_id']!=pid or m['policy_sha256']!=data['policies']['hatexplain/'+model]['sha256']:
                raise ValueError('Fresh run model/policy mismatch')
            expected=rows(state/'data/hatexplain'/(split+'.jsonl'));rr=rows(folder/'predictions.jsonl')
            if m['dataset_sha256']!=digest(state/'data/hatexplain'/(split+'.jsonl')) or completed['predictions_sha256']!=digest(folder/'predictions.jsonl'):
                raise ValueError('Changed data or score output')
            truth={r['id']:r for r in expected}
            if len(rr)!=len(truth) or {r['id'] for r in rr}!=truth.keys():raise ValueError('Incomplete fresh run')
            for r in rr:
                if any(r.get(k)!=truth[r['id']].get(k) for k in ('expected','group','prompt_sha256','source_label','split')):
                    raise ValueError('Fresh score metadata differs')
            record=dict(model=model,split=split,n=len(rr),errors=completed['errors'],wall_seconds=completed['wall_seconds'],
                predictions_sha256=digest(folder/'predictions.jsonl'),manifest_sha256=digest(folder/'manifest.json'))
            if split=='canary':
                old={r['id']:r for r in rows(HX/'runs'/f'{model}--{pid}--markdown--fit/predictions.jsonl.gz')}
                record['changed_decisions']=sum(r['prediction']!=old[r['id']]['prediction'] for r in rr)
                record['max_abs_score_difference']=max(abs(r['score']-old[r['id']]['score']) for r in rr if r['prediction']!='ERROR')
            else:
                score_path=state/'scores/hatexplain'/model/(split+'.jsonl.gz')
                write_rows(score_path,rr);record['stored_scores_sha256']=digest(score_path)
            audit.append(record)
    write(state/'ingestion.json',dict(created_utc=now(),runs=audit,registration_sha256=digest(state/'inference-registration.json')),exclusive=True)
    print(json.dumps({'new_development_observations':sum(r['n'] for r in audit),'errors':sum(r['errors'] for r in audit),
        'canary':[r for r in audit if r['split']=='canary']},indent=2))


def score_inputs(state,dataset,names,split):
    paths={name:Path(state)/'scores'/dataset/name/(split+'.jsonl.gz') for name in names}
    return {name:rows(p) for name,p in paths.items()}, {str(p.relative_to(state)):digest(p) for p in paths.values()}


def verify_development(state,dataset,names):
    data=read(state/'data-manifest.json')
    ingestion=read(state/'ingestion.json') if dataset=='hatexplain' else None
    for name in names:
        for split in ['fit','validation']:
            relative=f'scores/{dataset}/{name}/{split}.jsonl.gz'
            if dataset=='wildguard':expected=data['data_hashes'][relative]
            else:
                record=next(r for r in ingestion['runs'] if r['model']==name and r['split']==split)
                expected=record['stored_scores_sha256']
            if digest(state/relative)!=expected:raise ValueError('Unregistered development scores')


def test_sources(dataset,names):
    paths={}
    for name in names:
        source=WG/'runs'/f'{name}-test-{WG_RUNS[name]}'/'predictions.jsonl.gz' if dataset=='wildguard' else HX/'runs'/f'{name}--{HX_POLICIES[name]}--markdown--test'/'predictions.jsonl.gz'
        paths[name]=dict(path=str(source.relative_to(ROOT)),sha256=digest(source))
    if dataset=='wildguard':
        source=WG/'runs/wildguard-test-p0/predictions.jsonl.gz'
        paths['wildguard-baseline']=dict(path=str(source.relative_to(ROOT)),sha256=digest(source))
    return paths


def fit(state,cohort):
    state=Path(state);out=state/'cohorts'/cohort
    if out.exists():raise ValueError('Immutable cohort fit already exists')
    dataset,names=COHORTS[cohort]
    verify_development(state,dataset,names)
    tr,th=score_inputs(state,dataset,names,'fit');vr,vh=score_inputs(state,dataset,names,'validation')
    tm,X,y,valid=align(tr,names);vm,V,_,vvalid=align(vr,names);assert_disjoint(tm,vm)
    out.mkdir(parents=True);start=time.monotonic()
    candidates,selection=search(names,tm,X,y,valid,vm,V,vvalid)
    joblib.dump(candidates,out/'models.joblib',compress=3)
    write(out/'selection.json',selection,exclusive=True)
    freeze=dict(created_utc=now(),cohort=cohort,dataset=dataset,features=names,source_hashes=fitting_sources(),
        development_hashes={**th,**vh},models_sha256=digest(out/'models.joblib'),selection_sha256=digest(out/'selection.json'),
        data_manifest_sha256=digest(state/'data-manifest.json'),protocol_sha256=digest(ROOT/'docs/ensemble/PLAN.md'),
        policies={k:v for k,v in read(state/'data-manifest.json')['policies'].items() if k.startswith(dataset+'/')},
        test_sources=test_sources(dataset,names),fit_seconds=time.monotonic()-start,fit_n=len(tm),validation_n=len(vm),
        test_role='Exploratory reused official test. No test scores used in this fit or selection.')
    write(out/'freeze.json',freeze,exclusive=True)
    print(json.dumps(dict(cohort=cohort,fit_n=len(tm),validation_n=len(vm),primary=selection['primary'],best_single=selection['best_single'],best_ensemble=selection['best_ensemble'],freeze_sha256=digest(out/'freeze.json'))))


def verify_freeze(state,cohort):
    state=Path(state);out=state/'cohorts'/cohort;f=read(out/'freeze.json')
    if f['cohort']!=cohort or f['source_hashes']!=fitting_sources():raise ValueError('Changed frozen code or cohort')
    if f['models_sha256']!=digest(out/'models.joblib') or f['selection_sha256']!=digest(out/'selection.json'):
        raise ValueError('Changed learned model or selection')
    if f['data_manifest_sha256']!=digest(state/'data-manifest.json'):raise ValueError('Changed development manifest')
    for p,h in f['development_hashes'].items():
        if digest(state/p)!=h:raise ValueError('Changed fitting or validation scores')
    return f


def stage_test(state,cohort):
    state=Path(state);f=verify_freeze(state,cohort)
    for model,spec in f['test_sources'].items():
        source=ROOT/spec['path']
        if digest(source)!=spec['sha256']:raise ValueError('Frozen original test archive changed')
        target=state/'scores'/f['dataset']/model/'test.jsonl.gz';target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if digest(target)!=spec['sha256']:raise ValueError('Staged test differs')
        else:shutil.copy2(source,target)


def paired(meta,a,b,reps=2000):
    groups=sorted({r['group'] for r in meta});index={g:i for i,g in enumerate(groups)}
    counts=np.zeros((len(groups),2,4),dtype=int)
    for i,r in enumerate(meta):
        for j,p in enumerate((a[i],b[i])):
            k=(0 if p==1 else 3) if r['expected']=='BLOCK' else (1 if p==0 else 2)
            counts[index[r['group']],j,k]+=1
    rng=np.random.default_rng(SEED);values=[]
    for start in range(0,reps,100):
        draw=rng.integers(0,len(groups),size=(min(100,reps-start),len(groups)))
        summed=counts[draw].sum(axis=1)
        tp,tn,fp,fn=[summed[:,:,i] for i in range(4)]
        accuracy=(tp+tn)/(tp+tn+fp+fn)
        f1b=np.divide(2*tp,2*tp+fp+fn,out=np.zeros_like(tp,dtype=float),where=(2*tp+fp+fn)!=0)
        f1a=np.divide(2*tn,2*tn+fp+fn,out=np.zeros_like(tn,dtype=float),where=(2*tn+fp+fn)!=0)
        mf=(f1a+f1b)/2;values.extend(zip(accuracy[:,0]-accuracy[:,1],mf[:,0]-mf[:,1]))
    vals=np.array(values);ma=metrics(meta,a);mb=metrics(meta,b)
    gold=np.array([r['expected']=='BLOCK' for r in meta]);ac=a==gold;bc=b==gold
    return dict(accuracy_delta=ma['accuracy']-mb['accuracy'],macro_f1_delta=ma['macro_f1']-mb['macro_f1'],
        accuracy_ci95=np.quantile(vals[:,0],[.025,.975]).tolist(),macro_f1_ci95=np.quantile(vals[:,1],[.025,.975]).tolist(),
        cases_fixed=int((ac&~bc).sum()),cases_broken=int((bc&~ac).sum()),groups=len(groups),replicates=reps,
        limitation='Unadjusted descriptive intervals; exclude policy-search and inference uncertainty; tests reused from prior studies.')


def slices(meta,p):
    result={}
    for field in ['source_label','adversarial','subcategory','agreement','platform']:
        if not any(field in r for r in meta):continue
        result[field]={}
        for value in sorted({str(r.get(field)) for r in meta}):
            idx=[i for i,r in enumerate(meta) if str(r.get(field))==value]
            result[field][value]=metrics([meta[i] for i in idx],p[idx])
    return result


def evaluate(state,cohort):
    state=Path(state);out=state/'cohorts'/cohort;f=verify_freeze(state,cohort)
    if (out/'results.json').exists():raise ValueError('Official evaluation already exists')
    for model,spec in f['test_sources'].items():
        if digest(state/'scores'/f['dataset']/model/'test.jsonl.gz')!=spec['sha256']:raise ValueError('Changed staged test')
    data,_=score_inputs(state,f['dataset'],f['features'],'test')
    meta,X,y,valid=align(data,f['features'])
    train,_=score_inputs(state,f['dataset'],f['features'],'fit');val,_=score_inputs(state,f['dataset'],f['features'],'validation')
    assert_disjoint(align(train,f['features'])[0],align(val,f['features'])[0],meta)
    # Only load our own hash-verified locally produced model file.
    candidates=joblib.load(out/'models.joblib');selection=read(out/'selection.json')
    scored={};pred={};prediction_rows=[]
    for c in candidates:
        s=predict(c,X);p=classify(s,validity(c,valid),c['threshold']);pred[c['id']]=p
        scored[c['id']]=dict(family=c['family'],threshold=c['threshold'],metrics=metrics(meta,p,s))
        prediction_rows.extend(dict(r,candidate=c['id'],prediction='ERROR' if pp==-1 else 'BLOCK' if pp else 'ALLOW',score=float(ss)) for r,pp,ss in zip(meta,p,s))
    if f['dataset']=='wildguard':
        baseline={r['id']:r for r in rows(state/'scores/wildguard/wildguard-baseline/test.jsonl.gz')}
        if set(baseline)!={r['id'] for r in meta}:raise ValueError('WildGuard baseline population differs')
        for r in meta:
            if any(r[k]!=baseline[r['id']][k] for k in ['expected','group','prompt_sha256']):raise ValueError('Baseline metadata mismatch')
        p=np.array([{'ALLOW':0,'BLOCK':1,'ERROR':-1}[baseline[r['id']]['prediction']] for r in meta])
        pred['wildguard-baseline']=p;scored['wildguard-baseline']=dict(family='external',metrics=metrics(meta,p))
    def val_rank(r):return (-r['validation']['accuracy'],-r['validation']['macro_f1'],abs(r['selected_threshold']-.5),r['selected_threshold'],r['id'])
    per_single={name:min([r for r in selection['candidates'] if r['id'].startswith('single/'+name+'/')],key=val_rank)['id'] for name in f['features']}
    show=set(selection['selected'].values())|set(per_single.values())|{f'single/{n}/fixed' for n in f['features']}
    if 'wildguard-baseline' in scored:show.add('wildguard-baseline')
    for identifier in show:scored[identifier]['slices']=slices(meta,pred[identifier])
    contrasts={}
    for family,identifier in selection['selected'].items():
        if family=='single':continue
        contrasts[family]=dict(candidate=identifier,vs_best_single=paired(meta,pred[identifier],pred[selection['best_single']]))
        if 'wildguard-baseline' in pred:contrasts[family]['vs_wildguard']=paired(meta,pred[identifier],pred['wildguard-baseline'])
    error_pairs=[]
    for i,a in enumerate(f['features']):
        for b in f['features'][i+1:]:
            pa,pb=pred[per_single[a]],pred[per_single[b]];ca,cb=pa==y,pb==y
            error_pairs.append(dict(a=a,b=b,disagreements=int((pa!=pb).sum()),both_wrong=int((~ca&~cb).sum()),
                a_correct_b_wrong=int((ca&~cb).sum()),b_correct_a_wrong=int((cb&~ca).sum())))
    oracle=np.column_stack([pred[per_single[n]]==y for n in f['features']]).any(axis=1)
    highest=max((scored[c['id']]['metrics']['accuracy'],c['id']) for c in candidates if c['family']=='single')
    result=dict(created_utc=now(),cohort=cohort,freeze_sha256=digest(out/'freeze.json'),n=len(meta),selection=selection['selected'],
        primary=selection['primary'],best_single=selection['best_single'],best_ensemble=selection['best_ensemble'],per_model_selected=per_single,
        highest_observed_test_single=dict(candidate=highest[1],accuracy=highest[0],role='Descriptive hurdle only; never used to select ensemble'),
        all_candidates=scored,display_candidates=sorted(show),contrasts=contrasts,complementarity=error_pairs,
        hindsight_label_oracle=dict(accuracy=float(oracle.mean()),role='Non-deployable at-least-one-correct diagnostic, not a bound on score-based ensembles'),
        archived_mean_request_seconds={n:float(np.mean([r['latency_seconds'] for r in data[n]])) for n in f['features']},
        serving_note=f"Ensemble uses {len(f['features'])} base-model evaluations per item. Archived concurrent request timings are not production ensemble latency or cost.")
    write_rows(out/'test-predictions.jsonl.gz',prediction_rows);write(out/'results.json',result,exclusive=True)
    print(json.dumps(dict(cohort=cohort,primary=result['primary'],primary_accuracy=scored[result['primary']]['metrics']['accuracy'],
        best_single=result['best_single'],single_accuracy=scored[result['best_single']]['metrics']['accuracy'],
        best_ensemble=result['best_ensemble'],ensemble_accuracy=scored[result['best_ensemble']]['metrics']['accuracy'],
        primary_contrast=contrasts['logistic']),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['ingest','fit','stage-test','evaluate']);p.add_argument('--state',required=True);p.add_argument('--cohort',choices=list(COHORTS))
    a=p.parse_args()
    if a.action=='ingest':ingest(a.state)
    else:
        if not a.cohort:p.error('--cohort required')
        {'fit':fit,'stage-test':stage_test,'evaluate':evaluate}[a.action](a.state,a.cohort)
