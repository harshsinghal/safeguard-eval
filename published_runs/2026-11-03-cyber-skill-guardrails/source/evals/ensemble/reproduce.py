"""Verify an evidence bundle and refit/recompute all results without GPU inference."""
import argparse
from pathlib import Path

import joblib
import numpy as np

from evals.ensemble.common import COHORTS, align, assert_disjoint, digest, metrics, now, read, write
from evals.ensemble.learn import search, predict, classify, validity
from evals.ensemble.study import verify_freeze, score_inputs, paired


def close(actual, expected, path='root'):
    if isinstance(expected,dict):
        if set(actual)!=set(expected):raise AssertionError('Keys differ: '+path)
        for key in expected:close(actual[key],expected[key],path+'/'+key)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):raise AssertionError('Length differs: '+path)
        for i,(a,b) in enumerate(zip(actual,expected)):close(a,b,path+'/'+str(i))
    elif isinstance(expected,float):np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12,err_msg=path)
    elif actual!=expected:raise AssertionError('Values differ: '+path)


def reproduce(bundle, output, refit=True):
    bundle=Path(bundle);manifest=read(bundle/'checksums.json')
    for name,expected in manifest['sha256'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or digest(bundle/p)!=expected:raise ValueError('Bundle checksum mismatch: '+name)
    records=[]
    for cohort in COHORTS:
        f=verify_freeze(bundle,cohort);out=bundle/'cohorts'/cohort
        for model,spec in f['test_sources'].items():
            if digest(bundle/'scores'/f['dataset']/model/'test.jsonl.gz')!=spec['sha256']:raise ValueError('Test archive mismatch')
        train,_=score_inputs(bundle,f['dataset'],f['features'],'fit')
        val,_=score_inputs(bundle,f['dataset'],f['features'],'validation')
        test,_=score_inputs(bundle,f['dataset'],f['features'],'test')
        tm,X,y,tvalid=align(train,f['features']);vm,V,_,vvalid=align(val,f['features']);meta,T,_,testvalid=align(test,f['features'])
        assert_disjoint(tm,vm,meta)
        # The local evidence manifest and freeze must match before loading our artifact.
        candidates=joblib.load(out/'models.joblib');selection=read(out/'selection.json')
        if refit:
            fresh,selected=search(f['features'],tm,X,y,tvalid,vm,V,vvalid)
            close(selected,selection,'selection')
            if [c['id'] for c in fresh]!=[c['id'] for c in candidates]:raise AssertionError('Candidate list changed')
            for a,b in zip(fresh,candidates):
                if a['threshold']!=b['threshold']:raise AssertionError('Threshold changed')
                np.testing.assert_allclose(predict(a,T),predict(b,T),rtol=1e-10,atol=1e-12)
        result=read(out/'results.json');predictions={}
        for c in candidates:
            score=predict(c,T);p=classify(score,validity(c,testvalid),c['threshold']);predictions[c['id']]=p
            close(metrics(meta,p,score),result['all_candidates'][c['id']]['metrics'],'test/'+c['id'])
        if 'wildguard-baseline' in result['all_candidates']:
            from evals.ensemble.common import rows
            baseline={r['id']:r for r in rows(bundle/'scores/wildguard/wildguard-baseline/test.jsonl.gz')}
            predictions['wildguard-baseline']=np.array([{'ALLOW':0,'BLOCK':1,'ERROR':-1}[baseline[r['id']]['prediction']] for r in meta])
            close(metrics(meta,predictions['wildguard-baseline']),result['all_candidates']['wildguard-baseline']['metrics'],'baseline')
        for family,contrast in result['contrasts'].items():
            p=predictions[contrast['candidate']]
            close(paired(meta,p,predictions[result['best_single']]),contrast['vs_best_single'],'contrast/'+family)
            if 'vs_wildguard' in contrast:close(paired(meta,p,predictions['wildguard-baseline']),contrast['vs_wildguard'],'contrast/'+family+'/wildguard')
        records.append(dict(cohort=cohort,candidates=len(candidates),test_n=len(meta),
            refit_matches=refit,metrics_match=True,paired_intervals_match=True))
    write(output,dict(completed_utc=now(),status='passed',source='archived prompt-free scores; no model/API inference',
        bundle_files_verified=len(manifest['sha256']),cohorts=records))
    print('CPU reproduction passed: all fitted choices, test scores and paired intervals match.' if refit else 'Frozen-score reproduction passed.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--output',required=True);p.add_argument('--skip-refit',action='store_true')
    a=p.parse_args();reproduce(a.bundle,a.output,refit=not a.skip_refit)
