"""Immutable CPU-only log-odds follow-up; fit, freeze all cohorts, then test."""
import argparse
import json
from pathlib import Path
import shutil
import time

import joblib
import numpy as np

from evals.ensemble.common import ROOT,COHORTS,align,assert_disjoint,read,rows,write,write_rows,digest,now,metrics
from evals.ensemble.learn import classify,validity
from evals.ensemble.study import score_inputs,paired,slices
from evals.ensemble_logits.learn import search,predict,log_odds

PROTOCOL=ROOT/'docs/ensemble-logits/PLAN.md'


def source_hashes():
    paths=['evals/ensemble/common.py','evals/ensemble/learn.py','evals/ensemble/study.py',
           'evals/ensemble_logits/__init__.py','evals/ensemble_logits/learn.py','evals/ensemble_logits/study.py']
    return {name:digest(ROOT/name) for name in paths}


def assert_match(actual,expected,path='root'):
    if isinstance(expected,dict):
        if set(actual)!=set(expected):raise AssertionError('Different keys: '+path)
        for k in expected:assert_match(actual[k],expected[k],path+'/'+k)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):raise AssertionError('Different length: '+path)
        for i,(a,b) in enumerate(zip(actual,expected)):assert_match(a,b,path+'/'+str(i))
    elif isinstance(expected,float):np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12,err_msg=path)
    elif actual!=expected:raise AssertionError('Different value: '+path)


def verified_inventory(folder):
    folder=Path(folder);manifest=read(folder/'checksums.json')
    for name,expected in manifest['sha256'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or digest(folder/p)!=expected:raise ValueError('Changed evidence: '+name)
    return manifest


def copy_file(source,destination):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if digest(source)!=digest(destination):raise ValueError('Refusing changed artifact: '+str(destination))
    else:shutil.copy2(source,destination)


def audit(meta,scores,valid):
    values=scores[valid]
    log_odds(values)
    return dict(n=len(meta),groups=len({r['group'] for r in meta}),failed_model_outputs=int((~valid).sum()),
        minimum_score=float(values.min()),maximum_score=float(values.max()),boundary_scores=0)


def register(prior,state):
    prior,state=Path(prior),Path(state)
    if state.exists():raise ValueError('Registration destination already exists')
    verified_inventory(prior);state.mkdir(parents=True)
    inputs={};tests={};audits={}
    for source in sorted((prior/'scores').glob('*/*/*.gz')):
        relative=str(source.relative_to(prior))
        if source.name=='test.jsonl.gz':tests[relative]=digest(source)
        else:copy_file(source,state/relative);inputs[relative]=digest(source)
    for name in ['data-manifest.json','ingestion.json']:
        copy_file(prior/name,state/'provenance'/name);inputs['provenance/'+name]=digest(prior/name)
    copy_file(PROTOCOL,state/'PLAN.md');inputs['PLAN.md']=digest(PROTOCOL)
    for source in sorted((prior/'policies').rglob('*.json')):
        relative=str(source.relative_to(prior));copy_file(source,state/relative);inputs[relative]=digest(source)
    for cohort,(dataset,names) in COHORTS.items():
        for name in ['models.joblib','selection.json','freeze.json']:
            rel=f'reference/{cohort}/{name}';source=prior/'cohorts'/cohort/name
            copy_file(source,state/rel);inputs[rel]=digest(source)
        tests[f'reference/{cohort}/results.json']=digest(prior/'cohorts'/cohort/'results.json')
        tr,_=score_inputs(state,dataset,names,'fit');vr,_=score_inputs(state,dataset,names,'validation')
        tm,X,_,tv=align(tr,names);vm,V,_,vv=align(vr,names);assert_disjoint(tm,vm)
        audits[cohort]=dict(fit=audit(tm,X,tv),validation=audit(vm,V,vv))
    record=dict(created_utc=now(),prior_evidence='published_runs/2026-10-27-ensemble',prior_inventory_sha256=digest(prior/'checksums.json'),
        source_hashes=source_hashes(),input_hashes=inputs,test_hashes=tests,development_audit=audits,protocol_sha256=digest(PROTOCOL),
        new_gpu_or_api_calls=0,extra_paid_compute_usd=0,cumulative_spend_usd=12.50119753456,
        status='Exploratory extension after prior official test results were known; no new test evaluation yet')
    write(state/'registration.json',record,exclusive=True)
    print('Registered three unchanged development cohorts and code hashes; test inputs not staged.')


def verify_registration(state):
    state=Path(state);r=read(state/'registration.json')
    if r['source_hashes']!=source_hashes():raise ValueError('Registered code changed')
    for name,expected in r['input_hashes'].items():
        if digest(state/name)!=expected:raise ValueError('Registered input changed: '+name)
    return r


def fit(state,cohort):
    state=Path(state);registration=verify_registration(state);out=state/'cohorts'/cohort
    if out.exists():raise ValueError('Immutable cohort fit already exists')
    dataset,names=COHORTS[cohort]
    tr,_=score_inputs(state,dataset,names,'fit');vr,_=score_inputs(state,dataset,names,'validation')
    tm,X,y,tv=align(tr,names);vm,V,_,vv=align(vr,names);assert_disjoint(tm,vm)
    start=time.monotonic();new,selection=search(names,X,y,tv,vm,V,vv,read(state/'reference'/cohort/'selection.json'))
    out.mkdir(parents=True);joblib.dump(new,out/'models.joblib',compress=3);write(out/'selection.json',selection,exclusive=True)
    freeze=dict(created_utc=now(),cohort=cohort,dataset=dataset,features=names,fit_n=len(tm),validation_n=len(vm),
        registration_sha256=digest(state/'registration.json'),source_hashes=source_hashes(),
        models_sha256=digest(out/'models.joblib'),selection_sha256=digest(out/'selection.json'),
        protocol_sha256=registration['protocol_sha256'],prior_freeze_sha256=digest(state/'reference'/cohort/'freeze.json'),
        fit_seconds=time.monotonic()-start,scope='New combiners and calibrators only; no model or policy updates')
    write(out/'freeze.json',freeze,exclusive=True)
    print(json.dumps(dict(cohort=cohort,new_candidates=len(new),selected=selection['selected'],freeze_sha256=digest(out/'freeze.json'))))


def verify_freeze(state,cohort):
    state=Path(state);verify_registration(state);out=state/'cohorts'/cohort;f=read(out/'freeze.json')
    if f['cohort']!=cohort or f['registration_sha256']!=digest(state/'registration.json') or f['source_hashes']!=source_hashes():
        raise ValueError('Changed frozen registration or code')
    if f['models_sha256']!=digest(out/'models.joblib') or f['selection_sha256']!=digest(out/'selection.json'):
        raise ValueError('Changed frozen model or selection')
    return f


def stage_test(prior,state):
    prior,state=Path(prior),Path(state);r=verify_registration(state)
    for cohort in COHORTS:verify_freeze(state,cohort)
    if (state/'test-staging.json').exists():raise ValueError('Tests already staged')
    if digest(prior/'checksums.json')!=r['prior_inventory_sha256']:raise ValueError('Prior evidence inventory changed')
    for relative,expected in r['test_hashes'].items():
        if relative.startswith('reference/'):
            _,cohort,name=relative.split('/');source=prior/'cohorts'/cohort/name
        else:source=prior/relative
        if digest(source)!=expected:raise ValueError('Registered test reference changed')
        copy_file(source,state/relative)
    write(state/'test-staging.json',dict(created_utc=now(),all_cohorts_frozen=True,
        cohort_freezes={c:digest(state/'cohorts'/c/'freeze.json') for c in COHORTS}),exclusive=True)
    print('All three cohorts frozen; cached official tests staged without new inference.')


def verify_test_stage(state):
    state=Path(state);r=verify_registration(state);stage=read(state/'test-staging.json')
    for cohort,expected in stage['cohort_freezes'].items():
        if digest(state/'cohorts'/cohort/'freeze.json')!=expected:raise ValueError('Cohort changed after test staging')
    if set(stage['cohort_freezes'])!=set(COHORTS):raise ValueError('Not every cohort frozen')
    for name,expected in r['test_hashes'].items():
        if digest(state/name)!=expected:raise ValueError('Changed staged test: '+name)


def evaluation(state,cohort,new=None):
    """Pure result computation, reused for independent archived-source reproduction."""
    state=Path(state);f=verify_freeze(state,cohort);verify_test_stage(state)
    test,_=score_inputs(state,f['dataset'],f['features'],'test');meta,X,y,valid=align(test,f['features'])
    tr,_=score_inputs(state,f['dataset'],f['features'],'fit');vr,_=score_inputs(state,f['dataset'],f['features'],'validation')
    assert_disjoint(align(tr,f['features'])[0],align(vr,f['features'])[0],meta)
    out=state/'cohorts'/cohort
    if new is None:new=joblib.load(out/'models.joblib')
    previous=joblib.load(state/'reference'/cohort/'models.joblib')
    old_result=read(state/'reference'/cohort/'results.json')
    selection=read(out/'selection.json');selected=selection['selected']
    scored={};pred={};prediction_rows=[]
    for c in previous+new:
        s=predict(c,X);p=classify(s,validity(c,valid),c['threshold']);pred[c['id']]=p
        m=metrics(meta,p,s)
        if c['id'] in old_result['all_candidates']:assert_match(m,old_result['all_candidates'][c['id']]['metrics'],'unchanged baseline/'+c['id'])
        scored[c['id']]=dict(kind=c['kind'],threshold=c['threshold'],origin='prior' if c['id'] in old_result['all_candidates'] else 'logit extension',metrics=m)
        if c['id'] not in old_result['all_candidates']:
            prediction_rows.extend(dict(r,candidate=c['id'],prediction='ERROR' if pp==-1 else 'BLOCK' if pp else 'ALLOW',score=float(ss)) for r,pp,ss in zip(meta,p,s))
    if f['dataset']=='wildguard':
        rr=rows(state/'scores/wildguard/wildguard-baseline/test.jsonl.gz');lookup={r['id']:r for r in rr}
        if len(rr)!=len(lookup) or set(lookup)!={r['id'] for r in meta}:raise ValueError('WildGuard population differs')
        for r in meta:
            if any(r[k]!=lookup[r['id']][k] for k in ['expected','group','prompt_sha256']):raise ValueError('WildGuard metadata differs')
        p=np.array([{'ALLOW':0,'BLOCK':1,'ERROR':-1}[lookup[r['id']]['prediction']] for r in meta])
        pred['wildguard-baseline']=p;scored['wildguard-baseline']=dict(origin='prior',kind='external',metrics=metrics(meta,p))
        assert_match(scored['wildguard-baseline']['metrics'],old_result['all_candidates']['wildguard-baseline']['metrics'],'WildGuard baseline')
    show=set(selected['per_model'].values())|{selected[k] for k in ['primary','secondary','best_single','prior_probability_logistic','prior_best_single','prior_best_ensemble']}
    if 'wildguard-baseline' in scored:show.add('wildguard-baseline')
    for cid in show:scored[cid]['slices']=slices(meta,pred[cid])
    references={k:selected[k] for k in ['prior_probability_logistic','best_single','prior_best_single','prior_best_ensemble']}
    if 'wildguard-baseline' in scored:references['wildguard']='wildguard-baseline'
    contrasts={}
    for role in ['primary','secondary']:
        contrasts[role]={name:dict(candidate=selected[role],reference=cid,**paired(meta,pred[selected[role]],pred[cid])) for name,cid in references.items()}
    highest=max((value['metrics']['accuracy'],cid) for cid,value in scored.items() if cid.startswith(('single/','logit-single/')))
    result=dict(cohort=cohort,n=len(meta),freeze_sha256=digest(out/'freeze.json'),selection=selected,
        all_candidates=scored,display_candidates=sorted(show),contrasts=contrasts,test_score_audit=audit(meta,X,valid),
        highest_observed_test_single=dict(candidate=highest[1],accuracy=highest[0],role='Descriptive only; not used to select any method'),
        no_new_language_model_inference=True,extra_paid_compute_usd=0,
        limitations=['Reconstructed log-odds, not full original logits','Previously observed official tests','Unadjusted descriptive intervals','No matched fine-tuning or effort baseline'])
    return result,prediction_rows


def evaluate(state,cohort):
    state=Path(state);out=state/'cohorts'/cohort
    if (out/'results.json').exists():raise ValueError('Immutable test evaluation already exists')
    result,predictions=evaluation(state,cohort)
    write_rows(out/'test-predictions.jsonl.gz',predictions);write(out/'results.json',result,exclusive=True)
    write(out/'evaluation-completion.json',dict(created_utc=now(),results_sha256=digest(out/'results.json'),predictions_sha256=digest(out/'test-predictions.jsonl.gz')),exclusive=True)
    print(json.dumps(dict(cohort=cohort,selected=result['selection'],primary=result['all_candidates'][result['selection']['primary']]['metrics'],contrasts=result['contrasts']['primary']),indent=2))


def reproduce(state,output):
    state=Path(state);inventory=verified_inventory(state);records=[]
    for cohort,(dataset,names) in COHORTS.items():
        verify_freeze(state,cohort);tr,_=score_inputs(state,dataset,names,'fit');vr,_=score_inputs(state,dataset,names,'validation')
        tm,X,y,tv=align(tr,names);vm,V,_,vv=align(vr,names);assert_disjoint(tm,vm)
        new,selection=search(names,X,y,tv,vm,V,vv,read(state/'reference'/cohort/'selection.json'))
        assert_match(selection,read(state/'cohorts'/cohort/'selection.json'),'selection/'+cohort)
        result,predictions=evaluation(state,cohort,new=new)
        assert_match(result,read(state/'cohorts'/cohort/'results.json'),'result/'+cohort)
        saved=rows(state/'cohorts'/cohort/'test-predictions.jsonl.gz')
        assert_match(predictions,saved,'predictions/'+cohort)
        records.append(dict(cohort=cohort,new_candidates_refitted=len(new),test_n=result['n'],all_results_and_predictions_match=True))
    write(output,dict(completed_utc=now(),status='passed',inventory_files_verified=len(inventory['sha256']),cohorts=records,
        new_model_or_api_inference=0,extra_paid_compute_usd=0))
    print('CPU refit reproduction passed for all 58 new candidates, selected comparisons and test predictions.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','fit','stage-test','evaluate','reproduce'])
    p.add_argument('--state',required=True);p.add_argument('--prior');p.add_argument('--cohort',choices=list(COHORTS));p.add_argument('--output')
    a=p.parse_args()
    if a.action in ['register','stage-test']:
        if not a.prior:p.error('--prior is required')
        {'register':register,'stage-test':stage_test}[a.action](a.prior,a.state)
    elif a.action=='reproduce':
        if not a.output:p.error('--output is required')
        reproduce(a.state,a.output)
    else:
        if not a.cohort:p.error('--cohort is required')
        {'fit':fit,'evaluate':evaluate}[a.action](a.state,a.cohort)
