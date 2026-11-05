"""Matched-population metrics, clustered intervals, and text-free publication."""
import argparse
from collections import defaultdict
import shutil
from .common import *
from evals.leaderboard.metrics import bootstrap,interval

def summarize(state):
    state=Path(state);verify(state,test=True)
    selection=read(state/'selection.json')['models'];output={}
    lengths={(r['id'],r['model']):r['candidates'] for r in rows(state/'input-lengths.jsonl')}
    for task in TASKS:
        output[task]={}
        for cohort,models in (('primary',PRIMARY),('short',MODEL_NAMES)):
            allowed=set(read(state/'eligibility.json')['primary' if cohort=='primary' else 'policylm'])
            population=[metadata(r) for r in data(state,task,'test') if r['id'] in allowed]
            if not population:continue
            population=sorted(population,key=lambda r:r['id']);actual={r['id'] for r in population}
            results={};vectors={}
            for model in models:
                selected=selection[model][task]['selected']
                if selected is None:continue
                results[model]={}
                for arm,pid in [('initial','initial'),('selected',selected)]:
                    rr=[r for r in complete(state,model,task,'test',pid) if r['id'] in actual]
                    if [r['id'] for r in rr]!=[r['id'] for r in population]:raise ValueError('Unequal comparison population')
                    vectors[model+'/'+arm]=[{'ALLOW':0,'BLOCK':1,'ERROR':-1}[r['prediction']] for r in rr]
                    slices=defaultdict(list)
                    for r in rr:
                        slices['risk/'+r['risk_source']].append(r)
                        slices['action/'+r['action_kind']].append(r)
                        if r['expected']=='ALLOW':slices['safe_with_risk' if r['risk_present'] else 'safe_no_risk'].append(r)
                        # A shared tokenizer defines common length slices across models.
                        n=lengths[r['id'],'shieldstral']['initial']['tokens']
                        band='<=2k' if n<=2048 else '2k-4k' if n<=4096 else '4k-8k' if n<=8192 else '>8k'
                        slices['length/'+band].append(r)
                    results[model][arm]=dict(policy=pid,metrics=measures(rr),slices={k:measures(v) for k,v in sorted(slices.items())})
            draws=bootstrap(population,vectors,repetitions=2000) if len({r['expected'] for r in population})==2 else {}
            for model,arms in results.items():
                for arm,r in arms.items():
                    d=draws.get(model+'/'+arm,{})
                    r['intervals95']={m:interval(x) for m,x in d.items()}
                    if d:
                        r['intervals95']['false_positive_rate']=interval(1-d['specificity']) if not r['metrics']['unresolved'] else None
                        r['intervals95']['false_negative_rate']=interval(1-d['recall']) if not r['metrics']['unresolved'] else None
                a,b=arms['initial']['metrics'],arms['selected']['metrics']
                arms['change']=dict(balanced_accuracy=b['balanced_accuracy']-a['balanced_accuracy'] if a['balanced_accuracy'] is not None else None,
                    accuracy=b['accuracy']-a['accuracy'],false_flags=b['false_blocks']-a['false_blocks'],misses=b['missed_violations']-a['missed_violations'],
                    balanced_accuracy_interval95=interval(draws[model+'/selected']['balanced_accuracy']-draws[model+'/initial']['balanced_accuracy']) if draws else None)
            groups=defaultdict(list)
            for r in population:groups[r['group']].append(r['expected'])
            output[task][cohort]=dict(n=len(population),complete_input_coverage=len(population)/len(data(state,task,'test')),
                classes=dict(ALLOW=sum(r['expected']=='ALLOW' for r in population),BLOCK=sum(r['expected']=='BLOCK' for r in population)),
                groups=len(groups),mixed_label_heuristic_groups=sum(len(set(v))==2 for v in groups.values()),models=results)
    write(state/'results.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),freeze_sha256=digest(state/'freeze.json'),
        scope='Agreement with synthetic StepGuard SFT reference labels on scenario-grouped held-out splits; not live prevention or an official held-out benchmark.',results=output))
    for task,panels in output.items():
        for cohort,panel in panels.items():
            print(canonical(dict(task=task,cohort=cohort,n=panel['n'],models={m:dict(policy=x['selected']['policy'],
                accuracy=x['selected']['metrics']['accuracy'],balanced_accuracy=x['selected']['metrics']['balanced_accuracy'],
                false_flags=x['selected']['metrics']['false_blocks'],misses=x['selected']['metrics']['missed_violations'],
                errors=x['selected']['metrics']['unresolved'],change=x['change']) for m,x in panel['models'].items()})))

def export(state,destination):
    """Allowlisted, text-free artifacts; safe during registration and after results."""
    state=Path(state);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    patterns=('registration.json','authorization.json','data-audit.json','context-audit.json','development-review.json',
        'eligibility.json','input-lengths.jsonl','policy-token-lengths.json','group-edges.jsonl',
        'metadata/*/*.jsonl','policies/*/*.json','tokenizers/*.json','selection.json','freeze.json',
        'predictions/*/*/*/*.jsonl','results.json','jev-costs.json','billing.json','cleanup.json','amendments/*.json')
    files={}
    for pattern in patterns:
        for p in sorted(state.glob(pattern)):
            rel=p.relative_to(state);target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target);files[str(rel)]=digest(p)
    write(destination/'published-manifest.json',dict(created_utc=now(),files=files,
        raw_inputs='Private, reconstruct from the pinned source with evals.stepguard.data; never execute source tool calls.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['summarize','export']);p.add_argument('--state',required=True);p.add_argument('--destination')
    a=p.parse_args()
    if a.action=='summarize':summarize(a.state)
    else:
        if not a.destination:p.error('--destination required')
        export(a.state,a.destination)
