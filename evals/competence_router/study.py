"""Registered local preparation, paired guard collection, CPU fitting and evaluation."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gc
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import numpy as np
from evals.liquid_router.common import CATEGORIES, MODEL, REVISION, TRACK_CATEGORY
from evals.routed_guard.common import *
from evals.routed_guard.server import http, free_port
from evals.routed_guard.experiment import collect
from .model import Features, SEMANTIC_FIELDS, PROMPT_TOKENS, POLICY_TOKENS, probabilities, route, policy_contract_hash

SEED = 20261106
SPLITS = ('fit','validation','test')


def code_hashes():
    paths = list((ROOT/'evals/competence_router').glob('*.py'))
    paths += list((ROOT/'evals/routed_guard').glob('*.py'))
    paths += [ROOT/p for p in ('evals/liquid_router/model.py','evals/liquid_router/common.py',
        'evals/liquid_router/prepare.py','evals/liquid_router/study.py','docs/competence-router/PLAN.md',
        'tools/repeat_routed_guard_with_telemetry.py','evals/decision_models/vendor-hashes.json')]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}


def balanced(records, count):
    strata=defaultdict(list)
    for r in records: strata[(r['track'],r['expected'])].append(r)
    for rr in strata.values(): rr.sort(key=lambda r:sha(str(SEED)+r['id']))
    chosen=[]; used=Counter()
    while len(chosen)<count:
        progress=False
        for key in sorted(strata):
            while strata[key] and used[strata[key][0]['group']]>=2: strata[key].pop(0)
            if strata[key]:
                r=strata[key].pop(0); chosen.append(r); used[r['group']]+=1; progress=True
                if len(chosen)==count: break
        if not progress: raise ValueError('Insufficient stratified source support')
    return chosen


def prepare(state, liquid, pilot, pool_path):
    from evals.liquid_router.common import rows as load_rows
    from evals.liquid_router.prepare import purge_overlap
    state,liquid,pilot=map(Path,(state,liquid,pilot))
    if (state/'registration.json').exists(): raise ValueError('Preserve registered state')
    policies=read(ROOT/'benchmarks/enterprise-moderation/v0.1/policies.json')
    source={s:load_rows(liquid/'data'/(s+'.jsonl')) for s in ('fit','validation')}
    original_registration=read(liquid/'registration.json')
    for s,rr in source.items():
        if digest(liquid/'data'/(s+'.jsonl'))!=original_registration['input_hashes'][s]: raise ValueError('Original source drift')
    selected=[]
    for category in CATEGORIES:
        selected+=balanced([dict(r,role='fit') for r in source['fit'] if r['category']==category],64)
        for role,parity in (('validation',0),('test',1)):
            candidates=[dict(r,role=role) for r in source['validation'] if r['category']==category and int(sha(str(SEED)+r['audit_group'])[:8],16)%2==parity]
            selected+=balanced(candidates,16)
    pool=load_rows(pool_path); lookup={(r['track'],r['source_id']):r for r in pool}
    def convert(m,content,role):
        raw=lookup[(m['track'],m['source_id'])]
        return dict(id=m['id'],track=m['track'],category=TRACK_CATEGORY.get(m['track']),role=role,text=content,
            input_sha256=m['input_sha256'],expected=m['expected'],source_id=m['source_id'],
            group=(TRACK_CATEGORY.get(m['track']) or m['track'])+'::'+str(raw['source_group']))
    cal_inputs={r['id']:r for r in rows(pilot/'data/calibration.jsonl')}
    for m in rows(pilot/'public/metadata/calibration.jsonl'):
        selected.append(convert(m,cal_inputs[m['id']]['content'],'fit'))
    protected=[]
    for m in rows(ROOT/'benchmarks/enterprise-moderation/v0.1/evaluation.jsonl'):
        raw=lookup[(m['track'],m['source_id'])]; protected.append(convert(m,raw['prompt'],'protected'))
    selected,audit=purge_overlap(selected+protected)
    parts={s:sorted([r for r in selected if r['role']==s],key=lambda r:r['id']) for s in SPLITS}
    if any(len(parts[s])<90 for s in ('validation','test')): raise ValueError('Too few retained evaluation records')
    for a in SPLITS:
        for b in SPLITS:
            if a<b and {r['audit_group'] for r in parts[a]} & {r['audit_group'] for r in parts[b]}: raise ValueError('Cross-split groups')
    for split,rr in parts.items():
        meta=[]; data=[]
        for r in rr:
            pid=r['track']+'-v0'; ph=policy_hash(policies[pid])
            m={k:v for k,v in r.items() if k not in ('text','role')}
            m.update(policy_id=pid,policy_sha256=ph)
            meta.append(m); data.append(dict(id=r['id'],content=r['text'],policy_id=pid,
                input_sha256=r['input_sha256'],policy_sha256=ph))
        jsonl(state/'data'/(split+'.jsonl'),data);jsonl(state/'public/metadata'/(split+'.jsonl'),meta)
    # Development reuse is bound to the exact same adapter and model versions.
    old=read(pilot/'registration.json')
    if old['models']!=MODELS or old['policies_sha256']!=sha(canonical(policies)): raise ValueError('Pilot configuration drift')
    from evals.routed_guard.common import code_hashes as old_hashes
    if old['code_hashes']!=old_hashes(): raise ValueError('Native adapter changed since cached development outputs')
    fitting={r['id']:r for r in rows(state/'data/fit.jsonl')}
    reused={}
    for model in ORDER:
        pp=rows(pilot/'public/calibration'/(model+'.jsonl')); out=[]
        for p in pp:
            if p['id'] not in fitting: continue
            check_prediction(p,fitting[p['id']],model);out.append(p)
        jsonl(state/'public/guards/fit'/(model+'.jsonl'),out)
        reused[model]=dict(n=len(out),source_sha256=digest(pilot/'public/calibration'/(model+'.jsonl')))
    old_config=read(pilot/'config.private.json')
    config=dict(old_config,instance_id=uuid.uuid4().hex,runtime_dir=str((state/'runtime').resolve()),
        selection_path=str((state/'bootstrap-selection.json').resolve()),competence_checkpoint=str((state/'checkpoint').resolve()))
    write(state/'config.private.json',config)
    write(state/'bootstrap-selection.json',dict(default_model='clef',category_models={},selection_status='development_collection'))
    report=dict(splits={s:dict(n=len(rr),categories=dict(Counter(r['category'] or 'custom_policy' for r in rr)),
        tracks=dict(Counter(r['track'] for r in rr)),labels=dict(Counter(r['expected'] for r in rr)),
        groups=len({r['audit_group'] for r in rr})) for s,rr in parts.items()},
        overlap_audit=audit,development_reuse=reused,guard_versions=MODELS,
        model_features=['content','semantic policy fields','decision contract','input structure'],
        previous_exposure='Validation/test previously used for category-classifier validation; no claim of a universally blind benchmark',
        reserved_test='Whole audited groups from original validation pool; outcomes hidden until selection freeze',
        original_sources_sha256={s:digest(liquid/'data'/(s+'.jsonl')) for s in source},
        protected_original_evaluation=983,original_studies_unchanged=True)
    write(state/'public/data-audit.json',report)
    registration=dict(created_utc=datetime.now(timezone.utc).isoformat(),code_hashes=code_hashes(),
        data_hashes={s:digest(state/'data'/(s+'.jsonl')) for s in SPLITS},
        metadata_hashes={s:digest(state/'public/metadata'/(s+'.jsonl')) for s in SPLITS},
        data_audit_sha256=digest(state/'public/data-audit.json'),policies_sha256=sha(canonical(policies)),
        encoder=dict(model=MODEL,revision=REVISION,frozen=True),models=MODELS,
        protocol_sha256=digest(ROOT/'docs/competence-router/PLAN.md'),default_model='clef',seed=SEED,
        guard_collection_limit_seconds=5400,actual_routed_limit_seconds=1200)
    write(state/'registration.json',registration);write(state/'public/registration.json',registration)
    print(canonical(report['splits']),flush=True)


def verify(state):
    state=Path(state);r=read(state/'registration.json')
    if r['code_hashes']!=code_hashes(): raise ValueError('Registered code drift: preserve run and record amendment')
    for s in SPLITS:
        if digest(state/'data'/(s+'.jsonl'))!=r['data_hashes'][s] or digest(state/'public/metadata'/(s+'.jsonl'))!=r['metadata_hashes'][s]: raise ValueError('Registered data drift')
    if sha(canonical(read(state/'config.private.json')['policies']))!=r['policies_sha256']: raise ValueError('Policy drift')
    return r


def check_prediction(p,item,model):
    if any(p.get(k)!=item[k] for k in ('id','input_sha256','policy_sha256','policy_id')): raise ValueError('Unbound paired outcome')
    if p.get('model')!=model: raise ValueError('Guard identity mismatch')
    if p.get('status')=='ok':
        if p.get('model_id')!=MODELS[model]['model'] or p.get('model_revision')!=MODELS[model]['revision']: raise ValueError('Guard version mismatch')
    elif any(p.get(k) is not None and p[k]!=MODELS[model][v] for k,v in (('model_id','model'),('model_revision','revision'))):
        raise ValueError('Failed guard identity mismatch')
    if p.get('status')=='ok' and (not p.get('full_input_passed') or p.get('prediction') not in labels_for(item['policy_id'])): raise ValueError('Invalid native result')


def collect_guards(state, split):
    from tools.repeat_routed_guard_with_telemetry import DeviceSampler
    from evals.routed_guard.experiment import start
    state=Path(state);verify(state)
    if split=='test': verify_freeze(state)
    entry=start(state); base=entry['base']; inputs=rows(state/'data'/(split+'.jsonl'))
    clock=state/'collection-clock.json'
    if not clock.exists(): write(clock,dict(start_epoch=time.time(),limit_seconds=5400))
    remaining=read(clock)['start_epoch']+5400-time.time()
    if remaining<=0: raise TimeoutError('Registered collection wall-time budget exhausted')
    deadline=time.monotonic()+remaining
    with DeviceSampler(state/'public'/(split+'-device.jsonl'),base):
        try:
            for model in ORDER:
                output=collect(base,'/v1/guard',inputs,state/'public/guards'/split/(model+'.jsonl'),model,deadline)
                for p in output:check_prediction(p,next(r for r in inputs if r['id']==p['id']),model)
        finally: http(base,'/v1/unload',{},timeout=30)
    print('PAIRED GUARDS COMPLETE',split,len(inputs)*len(ORDER),flush=True)


def extract(state):
    state=Path(state);verify(state); config=read(state/'config.private.json'); features=Features()
    all_views={}; view_exclusions=[]
    for split in ('test','validation','fit'):
        inputs=rows(state/'data'/(split+'.jsonl')); xx=[]; traces=[]
        for i,r in enumerate(inputs):
            x,trace=features.one(r['content'],config['policies'][r['policy_id']],labels_for(r['policy_id']))
            # Detect identical bounded prompt+policy views even for differing full text.
            from .model import encode_pair
            ids,_=encode_pair(features.tokenizer,r['content'],config['policies'][r['policy_id']],labels_for(r['policy_id']))
            key=sha(canonical(ids)); other=all_views.get(key)
            allowed=not other or other[0]==split
            if not allowed:view_exclusions.append(dict(id=r['id'],split=split,protected_split=other[0],reason='identical_bounded_view'))
            else:all_views[key]=(split,r['id'])
            xx.append(x); traces.append(dict(id=r['id'],fit_allowed=allowed,**trace))
            if (i+1)%64==0 or i+1==len(inputs):print('FEATURES',split,i+1,'/',len(inputs),flush=True)
        p=state/'features';p.mkdir(exist_ok=True);np.save(p/(split+'.npy'),np.stack(xx));jsonl(state/'public/features'/(split+'.jsonl'),traces)
    features.save(state/'checkpoint');write(state/'public/view-audit.json',dict(exclusions=view_exclusions,
        resolution='Higher priority test > validation > fit; excluded rows masked from fitting/selection, test retained',
        feature_shapes={s:list(np.load(state/'features'/(s+'.npy')).shape) for s in SPLITS}))


def outcomes(state,split):
    state=Path(state); meta=rows(state/'public/metadata'/(split+'.jsonl')); inputs=rows(state/'data'/(split+'.jsonl'))
    preds={m:{r['id']:r for r in rows(state/'public/guards'/split/(m+'.jsonl'))} for m in ORDER}
    y=np.zeros((len(meta),len(ORDER)));mask=np.zeros_like(y,dtype=bool)
    if set(meta[i]['id'] for i in range(len(meta)))!={r['id'] for r in inputs}:raise ValueError('Metadata mismatch')
    for j,m in enumerate(ORDER):
        if set(preds[m])!={r['id'] for r in inputs}:raise ValueError('Incomplete paired outcomes')
        for i,(c,r) in enumerate(zip(meta,inputs)):
            if c['id']!=r['id']:raise ValueError('Order mismatch')
            p=preds[m][r['id']];check_prediction(p,r,m)
            y[i,j]=p.get('status')=='ok' and p['prediction']==c['expected']
            mask[i,j]=p.get('status')=='ok'
    return meta,preds,y,mask


def paired_interval(delta,groups,resamples=1000):
    delta=np.asarray(delta,dtype=float); by=defaultdict(list)
    for d,g in zip(delta,groups):by[g].append(d)
    if not by:return [-1.,1.]
    sums=np.array([sum(v) for v in by.values()]); counts=np.array([len(v) for v in by.values()])
    rng=np.random.default_rng(SEED); ix=rng.integers(len(by),size=(resamples,len(by)))
    means=sums[ix].sum(1)/counts[ix].sum(1)
    return [float(v) for v in np.quantile(means,[.05,.95])]


def choose_prob_routes(p,config,cases,policies):
    return [route(pp,config,policy_contract_hash(policies[c['policy_id']],labels_for(c['policy_id'])))[0] for pp,c in zip(p,cases)]


def route_correct(routes,y):return np.array([y[i,ORDER.index(m)] for i,m in enumerate(routes)])


def fit(state):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    state=Path(state);verify(state)
    if (state/'public/selection-freeze.json').exists():raise ValueError('Selection already frozen')
    config=read(state/'config.private.json'); policies=config['policies']
    training,_,yt,mt=outcomes(state,'fit'); validation,predv,yv,mv=outcomes(state,'validation')
    xt=np.load(state/'features/fit.npy');xv=np.load(state/'features/validation.npy')
    fit_allowed=np.array([r['fit_allowed'] for r in rows(state/'public/features/fit.jsonl')]); val_allowed=np.array([r['fit_allowed'] for r in rows(state/'public/features/validation.jsonl')])
    mt &= fit_allowed[:,None]; mv &= val_allowed[:,None]
    scaler=StandardScaler().fit(xt[fit_allowed]);zt=scaler.transform(xt);zv=scaler.transform(xv)
    candidate_heads=[]
    for c in (.01,.1,1.):
        coefs=[];intercepts=[]
        for j in range(len(ORDER)):
            keep=mt[:,j];target=yt[keep,j]
            if len(target)<16:raise ValueError('Insufficient valid fitting outcomes')
            if len(np.unique(target))<2:
                prior=(target.sum()+1)/(len(target)+2);coef=np.zeros(xt.shape[1]);intercept=math.log(prior/(1-prior))
            else:
                model=LogisticRegression(C=c,solver='lbfgs',max_iter=2000,random_state=SEED).fit(zt[keep],target)
                if model.n_iter_[0]>=2000:raise RuntimeError('Competence fit did not converge')
                coef=model.coef_[0];intercept=model.intercept_[0]
            coefs.append(coef.tolist());intercepts.append(float(intercept))
        head=dict(mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),coef=coefs,intercept=intercepts)
        p=probabilities(xv,head);clipped=np.clip(p,1e-7,1-1e-7)
        loss=float((-(yv*np.log(clipped)+(1-yv)*np.log(1-clipped)))[mv].mean())
        candidate_heads.append(dict(C=c,head=head,validation_log_loss=loss,validation_brier=float(((p-yv)**2)[mv].mean())))
    selected=min(candidate_heads,key=lambda h:(h['validation_log_loss'],h['C']));p=probabilities(xv,selected['head'])
    counts=Counter(c['policy_id'] for c,keep in zip(training,fit_allowed) if keep);vc=Counter(c['policy_id'] for c,keep in zip(validation,val_allowed) if keep)
    supported=sorted({policy_contract_hash(policies[pid],labels_for(pid)) for pid,n in counts.items() if n>=16 and vc[pid]>=8})
    base=dict(default_model='clef',supported_policy_hashes=supported);default=yv[:,ORDER.index('clef')]
    groups=[r['audit_group'] for r in validation];candidates=[]
    for margin in (0.,.05,.10,.20,1.01):
        enabled=[];evidence={}
        # Evaluate each challenger against Clef, then validate their combined route.
        for m in ORDER:
            if m=='clef':continue
            rc=dict(base,enabled_models=[m],switch_margin=margin)
            routes=choose_prob_routes(p,rc,validation,policies);switch=np.array([a==m for a in routes]) & val_allowed
            delta=yv[:,ORDER.index(m)]-default
            ci=paired_interval(delta[switch],[g for g,k in zip(groups,switch) if k])
            evidence[m]=dict(n=int(switch.sum()),paired_delta=float(delta[switch].mean()) if switch.any() else None,ci90=ci)
            if switch.sum()>=8 and ci[0]>0:enabled.append(m)
        rc=dict(base,enabled_models=enabled,switch_margin=margin)
        routes=choose_prob_routes(p,rc,validation,policies);correct=route_correct(routes,yv)
        delta=correct-default;ci=paired_interval(delta[val_allowed],[g for g,k in zip(groups,val_allowed) if k])
        switches=sum(m!='clef' for m,k in zip(routes,val_allowed) if k)
        accepted=switches>0 and ci[0]>0
        candidates.append(dict(config=rc,accuracy=float(correct[val_allowed].mean()),switches=switches,
            paired_delta=float(delta[val_allowed].mean()),ci90=ci,accepted=bool(accepted),per_guard=evidence))
    accepted=[c for c in candidates if c['accepted']]
    if accepted:chosen=max(accepted,key=lambda c:(c['accuracy'],-c['switches'],c['config']['switch_margin']))
    else:chosen=candidates[-1]
    # Conservative category control uses trusted policy semantics, not benchmark source IDs.
    conservative={};conservative_evidence={}
    for key in supported:
        indices=np.array([policy_contract_hash(policies[c['policy_id']],labels_for(c['policy_id']))==key for c in validation]) & val_allowed
        eligible=[]; evidence={}
        for m in ORDER:
            if m=='clef':continue
            delta=yv[:,ORDER.index(m)]-default;ci=paired_interval(delta[indices],[g for g,k in zip(groups,indices) if k])
            evidence[m]=dict(n=int(indices.sum()),paired_delta=float(delta[indices].mean()),ci90=ci)
            if indices.sum()>=8 and ci[0]>0:eligible.append(m)
        conservative[key]=max(eligible,key=lambda m:(float(yv[indices,ORDER.index(m)].mean()),-ORDER.index(m))) if eligible else 'clef'
        conservative_evidence[key]=evidence
    checkpoint=state/'checkpoint'
    artifacts={str(p.relative_to(checkpoint)):digest(p) for p in sorted(checkpoint.rglob('*')) if p.is_file()}
    metadata=dict(chosen['config'],head=selected['head'],models=MODELS,order=list(ORDER),
        encoder=dict(model=MODEL,revision=REVISION),feature_contract=dict(prompt_tokens=PROMPT_TOKENS,
        policy_tokens=POLICY_TOKENS,semantic_fields=list(SEMANTIC_FIELDS),structure_dimensions=10),artifact_hashes=artifacts,
        policy_scope='Exact semantic policy and decision contract validated; unknown policies use Clef',
        probabilities_scope='Development-fitted estimates, not safety guarantees')
    write(checkpoint/'competence.json',metadata)
    targets=[]
    for i,c in enumerate(training):targets.append(dict(id=c['id'],correctness={m:int(yt[i,j]) if mt[i,j] else None for j,m in enumerate(ORDER)}))
    jsonl(state/'public/fit-targets.jsonl',targets)
    calibration={}
    for j,m in enumerate(ORDER):
        keep=mv[:,j];q=p[keep,j];target=yv[keep,j]
        bins=[(q>=a)&(q<b if b<1 else q<=b) for a,b in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:])]
        calibration[m]=dict(n=int(keep.sum()),brier=float(((q-target)**2).mean()),
            ece10=float(sum(k.sum()/len(q)*abs(float(q[k].mean()-target[k].mean())) for k in bins if k.any())))
    write(state/'public/validation-selection.json',dict(calibration=calibration,head_candidates=[{k:v for k,v in h.items() if k!='head'} for h in candidate_heads],
        selected_C=selected['C'],route_candidates=candidates,selected_route=chosen,conservative_category=conservative,
        conservative_evidence=conservative_evidence,default_accuracy=float(default[val_allowed].mean()),
        valid_n=int(val_allowed.sum()),semantic_failure_masks={m:int((~mt[:,j]).sum()) for j,m in enumerate(ORDER)}))
    jsonl(state/'public/validation-estimates.jsonl',[dict(id=c['id'],correctness_probabilities={m:float(pp[j]) for j,m in enumerate(ORDER)}) for c,pp in zip(validation,p)])
    freeze=dict(created_utc=datetime.now(timezone.utc).isoformat(),registration_sha256=digest(state/'registration.json'),
        checkpoint_hashes={str(q.relative_to(checkpoint)):digest(q) for q in sorted(checkpoint.rglob('*')) if q.is_file()},
        selection_sha256=digest(state/'public/validation-selection.json'),
        development_outputs={s:{m:digest(state/'public/guards'/s/(m+'.jsonl')) for m in ORDER} for s in ('fit','validation')})
    write(state/'public/selection-freeze.json',freeze)
    print('FROZEN',canonical(dict(C=selected['C'],enabled_models=metadata['enabled_models'],switch_margin=metadata['switch_margin'],
        validation_default=float(default[val_allowed].mean()),validation_routed=chosen['accuracy'],supported_policies=len(supported))),flush=True)


def verify_freeze(state):
    state=Path(state);verify(state);freeze=read(state/'public/selection-freeze.json')
    if digest(state/'registration.json')!=freeze['registration_sha256'] or digest(state/'public/validation-selection.json')!=freeze['selection_sha256']:raise ValueError('Selection drift')
    for rel,h in freeze['checkpoint_hashes'].items():
        if digest(state/'checkpoint'/rel)!=h:raise ValueError('Checkpoint drift')
    for s,models in freeze['development_outputs'].items():
        for m,h in models.items():
            if digest(state/'public/guards'/s/(m+'.jsonl'))!=h:raise ValueError('Development outcome drift')
    return freeze


def metrics(cases,predictions):
    lookup={r['id']:r for r in predictions};strata=defaultdict(list);confusion=Counter();correct=[]
    for c in cases:
        p=lookup[c['id']];ok=p.get('status')=='ok' and p.get('prediction')==c['expected']
        correct.append(int(ok));strata[(c['track'],c['expected'])].append(int(ok))
        confusion[c['expected']+'->'+(p.get('prediction') if p.get('status')=='ok' else 'ERROR')]+=1
    tasks={t:float(np.mean([np.mean(v) for (tt,l),v in strata.items() if tt==t])) for t in sorted({c['track'] for c in cases})}
    return dict(n=len(cases),accuracy=float(np.mean(correct)),available_task_macro_recall=float(np.mean(list(tasks.values()))),
        tasks=tasks,confusion=dict(confusion),successful_guard_coverage=sum(p.get('status')=='ok' for p in predictions)/len(cases),
        official_enterprise_profiles=None,profile_limitation='Incomplete fixed suite task/class coverage; no renormalized official headline')


def evaluate(state,pilot):
    from evals.liquid_router.model import Router
    state,pilot=map(Path,(state,pilot));verify_freeze(state)
    settings=read(state/'config.private.json'); learned=read(state/'checkpoint/competence.json')
    selection=read(state/'public/validation-selection.json'); original_selection=read(pilot/'selection.json')
    classifier=Router(settings['router_checkpoint'],threads=4,int8=False)
    reports={}
    for split in ('test','pilot_diagnostic'):
        if split=='test':
            cases,preds,y,mask=outcomes(state,'test');data=rows(state/'data/test.jsonl')
            xx=np.load(state/'features/test.npy');pp=probabilities(xx,learned['head'])
        else:
            cases=rows(pilot/'public/metadata/test.jsonl');data=rows(pilot/'data/test.jsonl')
            preds={m:{r['id']:r for r in rows(pilot/'public/test-controls'/(m+'.jsonl'))} for m in ORDER}
            features=Features(state/'checkpoint');estimates=[]
            for r in data:
                x,_=features.one(r['content'],settings['policies'][r['policy_id']],labels_for(r['policy_id']));estimates.append(probabilities(x,learned['head']))
            pp=np.stack(estimates);del features;gc.collect()
        routed=choose_prob_routes(pp,learned,cases,settings['policies']);category=[];conservative=[];router_rows=[]
        for i,(c,r) in enumerate(zip(cases,data)):
            old=classifier.predict(r['content']);m,_=choose_model(old,original_selection);category.append(m)
            key=policy_contract_hash(settings['policies'][r['policy_id']],labels_for(r['policy_id']))
            conservative.append(selection['conservative_category'].get(key,'clef'))
            router_rows.append(dict(id=c['id'],input_sha256=c['input_sha256'],policy_sha256=c['policy_sha256'],
                selected_model=routed[i],category_model=m,conservative_model=conservative[-1],
                correctness_probabilities={m:float(v) for m,v in zip(ORDER,pp[i])}))
        arms={'clef':['clef']*len(cases),'original_category':category,'conservative_category':conservative,'competence':routed}
        rr={};baseline=np.array([int(preds['clef'][c['id']].get('status')=='ok' and preds['clef'][c['id']]['prediction']==c['expected']) for c in cases])
        for name,routes in arms.items():
            outputs=[preds[m][c['id']] for c,m in zip(cases,routes)];report=metrics(cases,outputs)
            correct=np.array([int(p.get('status')=='ok' and p['prediction']==c['expected']) for c,p in zip(cases,outputs)])
            report.update(model_counts=dict(Counter(routes)),paired_vs_clef=dict(corrected=int(((correct==1)&(baseline==0)).sum()),
                newly_wrong=int(((correct==0)&(baseline==1)).sum()),delta=float((correct-baseline).mean()),
                ci90=paired_interval(correct-baseline,[c['audit_group'] if 'audit_group' in c else c['group'] for c in cases])))
            rr[name]=report
        reports[split]=dict(arms=rr,scope='Reserved competence holdout' if split=='test' else 'Previously exposed pilot; diagnostic only',
            guard_controls={m:metrics(cases,[preds[m][c['id']] for c in cases]) for m in ORDER},
            oracle_any_guard_correct=sum(any(preds[m][c['id']].get('status')=='ok' and preds[m][c['id']]['prediction']==c['expected'] for m in ORDER) for c in cases)/len(cases))
        jsonl(state/'public'/(split+'-routes.jsonl'),router_rows)
    write(state/'public/results.json',reports)
    print(canonical({s:{a:r['accuracy'] for a,r in v['arms'].items()} for s,v in reports.items()}),flush=True)


def actual(state):
    from tools.repeat_routed_guard_with_telemetry import DeviceSampler
    state=Path(state);verify_freeze(state);receipt=state/'competence-gateway.private.json'
    if receipt.exists():raise ValueError('Preserve existing gateway receipt')
    port=free_port();log=(state/'competence-gateway.private.log').open('w')
    proc=subprocess.Popen([sys.executable,'-B','-m','evals.competence_router.server','--config',str((state/'config.private.json').resolve()),'--port',str(port)],
        cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,HF_HUB_OFFLINE='1'))
    base='http://127.0.0.1:'+str(port);write(receipt,dict(base=base,pid=proc.pid))
    try:
        for _ in range(600):
            if proc.poll() is not None:raise RuntimeError('Competence gateway startup failed')
            try:
                if http(base,'/health',timeout=1).get('status')=='ready':break
            except OSError:pass
            time.sleep(.25)
        else:raise TimeoutError('Competence gateway startup timeout')
        inputs={r['id']:r for r in rows(state/'data/test.jsonl')};planned=rows(state/'public/test-routes.jsonl')
        with DeviceSampler(state/'public/actual-device.jsonl',base):
            try:
                deadline=time.monotonic()+1200
                for m in ORDER:
                    jobs=[inputs[p['id']] for p in planned if p['selected_model']==m]
                    if jobs:collect(base,'/v1/moderate',jobs,state/'public/actual-routed.jsonl',deadline=deadline)
            finally:http(base,'/v1/unload',{},timeout=30)
    finally:
        import signal
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        log.close()
        write(state/'public/cleanup.json',dict(competence_gateway_stopped=True,gpu_workers_unloaded=True,paid_compute_usd=0,hardware_clock_or_power_changes=False))
    cases,preds,_,_=outcomes(state,'test'); output=rows(state/'public/actual-routed.jsonl');out={r['id']:r for r in output}
    if set(out)!={c['id'] for c in cases}:raise ValueError('Incomplete actual system evaluation')
    plans={p['id']:p for p in planned};disagreements=0
    for c in cases:
        r=out[c['id']];plan=plans[c['id']];m=plan['selected_model']
        check_prediction(r,inputs[c['id']],r['model'])
        if not r.get('guard_attempted') or r['requested_model']!=m:raise ValueError('Mandatory dispatch mismatch')
        disagreements+=r['prediction']!=preds[m][c['id']]['prediction']
    result=metrics(cases,output);lat=[r['latency_ms'] for r in output]
    result.update(control_decision_changes=disagreements,guard_attempt_coverage=sum(bool(r.get('guard_attempted')) for r in output)/len(cases),
        actual_latency_ms={k:float(np.quantile(lat,q)) for k,q in (('p50',.5),('p95',.95),('p99',.99))},
        latency_scope='Actual CPU router plus single native guard, cooldown, HTTP and cold loads; grouped scheduling, not natural traffic')
    write(state/'public/actual-results.json',result);print('ACTUAL',canonical(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','collect','extract','fit','evaluate','actual']);p.add_argument('--state',required=True)
    p.add_argument('--liquid');p.add_argument('--pilot');p.add_argument('--pool');p.add_argument('--split',choices=SPLITS)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.state,a.liquid,a.pilot,a.pool)
    elif a.action=='collect':collect_guards(a.state,a.split)
    elif a.action=='evaluate':evaluate(a.state,a.pilot)
    else:globals()[a.action](a.state)
