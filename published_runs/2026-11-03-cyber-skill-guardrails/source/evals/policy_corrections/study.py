"""Development-only selection, staged freezes and deterministic evaluation."""
import argparse
from pathlib import Path
import numpy as np
from .common import (ROOT,MODELS,POLICIES,read,rows,write,digest,now,sources,labels,
                     check_registration,load_output,output_path)
from evals.leaderboard.metrics import select,decisions,metrics,bootstrap,interval


def register(state):
    state=Path(state)
    if (state/'outputs').exists():raise ValueError('Register before inference')
    files=[state/x for x in ['data-manifest.json','authoring.json','error-review.json',
                            'discovery-errors.jsonl.gz','discovery-summary.json','prior-use-audit.json']]
    files+=list((state/'policies').glob('*.json'))+list((state/'metadata').glob('*'))
    write(state/'registration.json',dict(created_utc=now(),sources=sources(),
        artifacts={str(p.relative_to(state)):digest(p) for p in files}),exclusive=True)


def validation_selection(state,model,policies):
    candidates={};metadata=None
    for policy in policies:
        m,c=load_output(state,model,policy,'validation')
        if metadata is not None and metadata!=m:raise ValueError('Misaligned validation')
        metadata=m;candidates[policy]=c
    per_policy={}
    for pid,candidate in candidates.items():
        choices,grid=select(labels(metadata),{pid:candidate})
        per_policy[pid]=dict(choices=choices,grid=grid)
    joint,joint_grid=select(labels(metadata),{pid:c for pid,c in candidates.items() if pid!='p0'})
    return dict(per_policy=per_policy,revision_choices=joint,revision_grid=joint_grid)


def select_shield(state):
    state=Path(state);check_registration(state)
    if (state/'shield-selection.json').exists():raise ValueError('Selection already frozen')
    validation=validation_selection(state,'shieldstral',POLICIES)
    selected=validation['revision_choices']['balanced']['candidate']
    discovery={}
    for pid in POLICIES:
        m,c=load_output(state,'shieldstral',pid,'discovery')
        discovery[pid]=metrics(labels(m),decisions(c,.5),c['score'])
    old=read(ROOT/'published_runs/2026-10-30-shield-probe/feature-provenance/shieldstral/fit/records.json')
    m,baseline=load_output(state,'shieldstral','p0','discovery')
    if [r['id'] for r in old]!=[r['id'] for r in m]:raise ValueError('Cached baseline identity mismatch')
    delta=float(np.max(np.abs(np.array(baseline['score'])-np.array([r['native_score'] for r in old]))))
    if delta>.002:raise ValueError('Fresh baseline differs materially from discovery scores')
    artifacts={str(p.relative_to(state)):digest(p) for p in (state/'outputs/shieldstral').glob('*/*.json')}
    write(state/'shield-selection.json',dict(created_utc=now(),selected_revision=selected,
        registration_sha256=digest(state/'registration.json'),artifacts=artifacts,
        validation=validation,discovery=discovery,cached_baseline_max_absolute_difference=delta),exclusive=True)
    print('SHIELD_SELECTED',selected,'validation BA',validation['revision_choices']['balanced']['metrics']['balanced_accuracy'])


def freeze(state):
    state=Path(state);check_registration(state);shield=read(state/'shield-selection.json')
    if shield['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Changed selection registration')
    for p,h in shield['artifacts'].items():
        if digest(state/p)!=h:raise ValueError('Changed Shieldstral selection evidence')
    selected=shield['selected_revision'];models={}
    for model in MODELS:
        result=shield['validation'] if model=='shieldstral' else validation_selection(state,model,['p0',selected])
        pp=result['per_policy']
        models[model]=dict(validation=result,
            primary={'baseline-native':dict(policy='p0',threshold=.5),
                'baseline-tuned':dict(policy='p0',threshold=pp['p0']['choices']['balanced']['threshold']),
                'revised-native':dict(policy=selected,threshold=.5),
                'revised-tuned':dict(policy=selected,threshold=pp[selected]['choices']['balanced']['threshold'])},
            operating={profile:{pid:pp[pid]['choices'][profile] for pid in ['p0',selected]}
                       for profile in ['false_block_limit','catch_target']})
    paths=[state/'shield-selection.json',state/'registration.json']+list((state/'outputs').glob('*/*/*.json'))
    f=dict(created_utc=now(),selected_revision=selected,models=models,
        artifacts={str(p.relative_to(state)):digest(p) for p in paths},
        note='No holdout/test outputs entered policy or cutoff selection. Qwen received the frozen Shieldstral revision.')
    write(state/'freeze.json',f,exclusive=True)
    print('FINAL_FREEZE',selected)


def check_freeze(state):
    state=Path(state);check_registration(state);f=read(state/'freeze.json')
    for p,h in f['artifacts'].items():
        if digest(state/p)!=h:raise ValueError('Frozen artifact changed: '+p)
    return f


def score_metrics(y,p,s):
    m=metrics(y,p,s)
    if all(x is not None for x in s) and not (p==-1).any():
        a=np.clip(np.array(s),1e-7,1-1e-7)
        m.update(brier=float(np.mean((a-y)**2)),log_loss=float(-np.mean(y*np.log(a)+(1-y)*np.log(1-a))))
    return m


def result_payload(state):
    state=Path(state);f=check_freeze(state);result={}
    for split in ['holdout','test']:
        predictions={};primary={};operating={};raw={};metadata=None
        for model,spec in f['models'].items():
            candidates={}
            for pid in ['p0',f['selected_revision']]:
                m,c=load_output(state,model,pid,split)
                if metadata is not None and metadata!=m:raise ValueError('Misaligned final population')
                metadata=m;candidates[pid]=c;raw[model+'/'+pid]=c
            y=labels(metadata);primary[model]={};operating[model]={}
            for name,cfg in spec['primary'].items():
                c=candidates[cfg['policy']];p=decisions(c,cfg['threshold']);predictions[model+'/'+name]=p
                primary[model][name]=dict(**cfg,metrics=score_metrics(y,p,c['score']))
            for profile,policies in spec['operating'].items():
                operating[model][profile]={}
                for pid,choice in policies.items():
                    if choice is None:operating[model][profile][pid]=None;continue
                    c=candidates[pid];p=decisions(c,choice['threshold'])
                    operating[model][profile][pid]=dict(threshold=choice['threshold'],validation=choice['metrics'],
                        metrics=score_metrics(y,p,c['score']))
        draws=bootstrap(metadata,predictions,repetitions=2000)
        ci={k:{metric:interval(v) for metric,v in dd.items()} for k,dd in draws.items()}
        pairs=[]
        for model in MODELS:
            for left,right in [('revised-tuned','baseline-tuned'),('revised-native','baseline-native'),('baseline-tuned','baseline-native')]:
                a,b=model+'/'+left,model+'/'+right
                diff=primary[model][left]['metrics']['balanced_accuracy']-primary[model][right]['metrics']['balanced_accuracy']
                pairs.append(dict(model=model,method=left,comparator=right,balanced_accuracy_delta=diff,
                    ci95=interval(draws[a]['balanced_accuracy']-draws[b]['balanced_accuracy']),
                    corrected=int(((predictions[a]==y)&(predictions[b]!=y)).sum()),
                    newly_wrong=int(((predictions[a]!=y)&(predictions[b]==y)).sum())))
        slices={}
        for field in ['subcategory','adversarial']:
            slices[field]={}
            for value in sorted({str(r[field]) for r in metadata}):
                ix=np.array([str(r[field])==value for r in metadata])
                slices[field][value]={name:metrics(y[ix],p[ix]) for name,p in predictions.items()}
        result[split]=dict(primary=primary,operating=operating,ci95=ci,paired_comparisons=pairs,slices=slices,
            n=len(metadata),groups=len({r['group'] for r in metadata}))
    return dict(freeze_sha256=digest(state/'freeze.json'),selected_revision=f['selected_revision'],
        datasets=result,bootstrap_repetitions=2000)


def evaluate(state):
    state=Path(state);r=result_payload(state);write(state/'results.json',r,exclusive=True)
    for split,data in r['datasets'].items():
        for model,configs in data['primary'].items():
            for name,row in configs.items():
                m=row['metrics'];print(split,model,name,round(m['balanced_accuracy']*100,3),'FP',m['false_blocks'],'FN',m['missed_violations'])


def verify(state):
    state=Path(state);f=check_freeze(state);s=read(state/'shield-selection.json')
    if validation_selection(state,'shieldstral',POLICIES)!=s['validation']:raise ValueError('Shieldstral selection reproduction')
    for model in MODELS:
        policies=POLICIES if model=='shieldstral' else ['p0',f['selected_revision']]
        if validation_selection(state,model,policies)!=f['models'][model]['validation']:raise ValueError('Final selection reproduction')
    if result_payload(state)!=read(state/'results.json'):raise ValueError('Result reproduction')
    print('Verified both datasets, all selections, operating profiles, slices and 12 paired bootstrap contrasts')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','select_shield','freeze','evaluate','verify'])
    p.add_argument('--state',required=True);a=p.parse_args();globals()[a.action](a.state)
