"""Immutable registration and validation-only policy selection."""
import argparse
from .common import *

def register(state):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    audit=read(state/'context-audit.json')
    # Verify separation across both evaluation tracks, including discovery rows.
    groups={s:set() for s in SPLITS}
    for task in TASKS:
        for split in SPLITS:
            groups[split].update(r['group'] for r in data(state,task,split))
    if any(groups[a]&groups[b] for i,a in enumerate(SPLITS) for b in SPLITS[i+1:]):
        raise ValueError('Scenario leakage across splits')
    authorization=dict(approved=True,experiment_cap_usd=8.0,gpu_and_storage_cap_usd=6.0,jev_cap_usd=2.0,
        prior_remaining_usd=9.053013164,basis='User approved implementing the StepGuard plan; existing unused benchmark authorization, not new credit.',
        created_utc=now())
    write(state/'authorization.json',authorization)
    files={}
    for pattern in ('data/*/*.jsonl','metadata/*/*.jsonl','policies/*/*.json','tokenizers/*.json',
                    'eligibility.json','input-lengths.jsonl','policy-token-lengths.json','context-audit.json',
                    'data-audit.json','development-review.json','group-edges.jsonl','authorization.json'):
        for p in sorted(state.glob(pattern)):files[str(p.relative_to(state))]=digest(p)
    if not audit['primary_n']:raise ValueError('No primary complete-input cohort')
    write(state/'registration.json',dict(created_utc=now(),sources=sources(),files=files,models=MODELS,
        primary=PRIMARY,seed=SEED,bootstrap_seed=20261029,bootstrap_repetitions=2000,
        source_revision=DATA_REVISION,source_sha256=DATA_SHA256,
        selection='validation balanced accuracy, shorter native policy representation, lexical candidate ID; no test-dependent changes',
        no_evaluable_validation='If no complete validation examples, skip that model/task; if one class only, retain initial without selection.'))
    print(canonical(dict(registered=digest(state/'registration.json'),coverage=audit['by_task_split'])),flush=True)

def freeze(state):
    state=Path(state);verify(state)
    if (state/'freeze.json').exists():raise ValueError('Already frozen')
    lengths=read(state/'policy-token-lengths.json');selections={};files={}
    for model in MODEL_NAMES:
        selections[model]={}
        for task in TASKS:
            population=data(state,task,'validation',model)
            if not population:
                selections[model][task]=dict(selected=None,reason='No complete validation examples',candidates={})
                continue
            candidates={}
            for pid in read(state/f'policies/{task}/{model}.json'):
                rr=complete(state,model,task,'validation',pid)
                rel=f'predictions/{model}/{task}/validation/{pid}.jsonl';files[rel]=digest(state/rel)
                native_length=lengths[model][task][pid]
                if model=='jev':
                    # Same fixed content; reported usage includes the actual serialized policy.
                    native_length=rr[0].get('usage',{}).get('input_tokens')
                    if native_length is None:native_length=10**12
                candidates[pid]=dict(metrics=measures(rr),tie_length=native_length)
            if len({r['expected'] for r in population})!=2:
                selected='initial';reason='Single validation class; retain initial, no optimization claim'
            else:
                selected=min(candidates,key=lambda p:(-candidates[p]['metrics']['balanced_accuracy'],candidates[p]['tie_length'],p))
                reason='Highest validation balanced accuracy, with preregistered ties'
            selections[model][task]=dict(selected=selected,reason=reason,candidates=candidates)
    write(state/'selection.json',dict(created_utc=now(),models=selections))
    files['selection.json']=digest(state/'selection.json')
    write(state/'freeze.json',dict(created_utc=now(),registration_sha256=digest(state/'registration.json'),files=files))
    print(canonical({m:{t:x['selected'] for t,x in v.items()} for m,v in selections.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','freeze']);p.add_argument('--state',required=True)
    a=p.parse_args();globals()[a.action](a.state)
