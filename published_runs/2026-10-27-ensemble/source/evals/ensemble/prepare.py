"""Audit development reuse and prepare fresh, pinned HateXplain inputs."""
import argparse
from collections import Counter
from pathlib import Path
import shutil

from evals.ensemble.common import (ROOT, WG, HX, WG_RUNS, HX_POLICIES, SEED, read, rows, write,
    write_rows, digest, now, partition, assert_disjoint)


def counts(rr):
    return dict(n=len(rr),groups=len({r['group'] for r in rr}),labels=dict(Counter(r['expected'] for r in rr)),
                source_labels=dict(Counter(r.get('source_label',r.get('subcategory')) for r in rr)))


def prepare(state, prior_work):
    state, prior_work = Path(state).resolve(), Path(prior_work).resolve()
    if (state/'data-manifest.json').exists(): raise ValueError('Preparation already exists')
    state.mkdir(parents=True,exist_ok=True)
    records={}; policies={}; sources={}
    def record(p):
        sources[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)] = digest(p)
    index={e['run']:e for e in read(WG/'run-index.json')}
    wg_pred={}
    for model,p in WG_RUNS.items():
        folder=WG/'runs'/f'{model}-fit-final-{p}'
        source=folder/'predictions.jsonl.gz'
        if digest(source)!=index[folder.name]['public_predictions_gzip_sha256']:
            raise ValueError('Changed frozen WildGuard score archive')
        wg_pred[model]=rows(source); record(source)
        policy=folder/'policy.json'; m=read(folder/'manifest.json')
        if digest(policy)!=m['policy_sha256']:raise ValueError('Changed frozen policy')
        dest=state/'policies/wildguard'/f'{model}.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(policy,dest)
        policies['wildguard/'+model]={'policy_id':m['policy_id'],'sha256':digest(policy),'revision':m['revision']}
    ids={r['id'] for r in wg_pred['policylm']}
    if any({r['id'] for r in rr}!=ids for rr in wg_pred.values()):raise ValueError('Cached training populations differ')
    used_groups=set(); used_ids=set(); used_hashes=set(); excluded_runs=[]
    for bundle in ['2026-10-24-wildguard','2026-10-25-qwen','2026-10-25-policy-transfer','2026-10-25-frontier-pilot']:
        for p in sorted((ROOT/'published_runs'/bundle).glob('**/manifest.json')):
            m=read(p)
            if m.get('split')=='test' or m.get('stage')=='fit-final' or 'fit-final' in p.parent.name:
                continue
            pp=p.with_name('predictions.jsonl.gz')
            if not pp.exists():pp=p.with_name('predictions.jsonl')
            if not pp.exists():continue
            rr=[r for r in rows(pp) if r.get('split')!='test' and str(r['id']).startswith('wgtrain-')]
            if not rr:continue
            used_groups.update(r['group'] for r in rr);used_ids.update(r['id'] for r in rr)
            used_hashes.update(r['prompt_sha256'] for r in rr if 'prompt_sha256' in r)
            excluded_runs.append({'path':str(pp.relative_to(ROOT)),'sha256':digest(pp),'n':len(rr)})
    assignments={r['id']:r for r in rows(WG/'training-assignments.jsonl.gz')}
    overlap=read(WG/'train-test-overlap.json')
    overlap_ids={i for r in overlap['rows'] for i in r['train_ids']}
    overlap_groups={assignments[i]['group'] for i in overlap_ids}
    eligible=[r for r in wg_pred['policylm'] if r['group'] not in used_groups|overlap_groups
              and r['id'] not in used_ids and r['prompt_sha256'] not in used_hashes]
    fit,val=partition(eligible)
    assert_disjoint(fit,val)
    for split,chosen in [('fit',fit),('validation',val)]:
        chosen_ids={r['id'] for r in chosen}
        for model,rr in wg_pred.items():
            out=[dict(r,ensemble_split=split) for r in rr if r['id'] in chosen_ids]
            write_rows(state/'scores/wildguard'/model/(split+'.jsonl.gz'),out)
    records['wildguard']=dict(cached_rows=len(ids),excluded_development_groups=len(used_groups),
        known_test_overlap_groups=len(overlap_groups),eligible=counts(eligible),fit=counts(fit),validation=counts(val),
        exclusions=excluded_runs,grouping=read(WG/'training-data-manifest.json')['grouping'],
        note='Earlier final-fit aggregate results were published; these rows were not used for policy search. Reused official tests remain exploratory.')

    from evals.hatexplain.data import EXPECTED,majority
    from evals.wildguard.data import group_prompts,sha
    source=prior_work/'hatexplain-run/source'
    for name,h in EXPECTED.items():
        if digest(source/name)!=h:raise ValueError('HateXplain publisher source changed')
        record(source/name)
    raw=read(source/'dataset.json'); divisions=read(source/'post_id_divisions.json')
    all_rows=[]
    for split,identifiers in divisions.items():
        for identifier in identifiers:
            post=raw[identifier];label,agreement=majority([a['label'] for a in post['annotators']])
            text=' '.join(post['post_tokens'])
            targets=Counter(t for a in post['annotators'] for t in set(a['target']))
            all_rows.append(dict(id=identifier,prompt=text,prompt_sha256=sha(text),expected='BLOCK' if label=='hatespeech' else 'ALLOW',
                source_label=label,agreement=agreement,targets=sorted(t for t,n in targets.items() if n>=2),
                original_split=split,platform='gab' if identifier.endswith('_gab') else 'twitter'))
    grouping=group_prompts(all_rows)
    for r in all_rows:r['group']=r['group'].replace('wg-','hx-',1)
    old_fit=rows(HX/'runs/policylm--p0--markdown--fit/predictions.jsonl.gz')
    examples=set(read(ROOT/'docs/hatexplain/data-manifest.json')['example_ids'])
    old_ids={r['id'] for r in old_fit}|examples
    excluded_groups={r['group'] for r in all_rows if r['original_split']!='train' or r['id'] in old_ids}
    eligible=[r for r in all_rows if r['original_split']=='train' and r['group'] not in excluded_groups]
    fit,val=partition(eligible)
    test=[r for r in all_rows if r['original_split']=='test']
    assert_disjoint(fit,val,test)
    reg=read(ROOT/'evals/hatexplain/registry.json')
    for split,chosen in [('fit',fit),('validation',val)]:
        write_rows(state/'data/hatexplain'/(split+'.jsonl'),[dict(r,split=split) for r in chosen])
    # A fixed old-fitting canary checks adapter consistency, not policy quality.
    old_lookup={r['id']:r for r in all_rows}
    canary=[dict(old_lookup[r['id']],split='canary') for r in sorted(old_fit,key=lambda r:r['id'])[:32]]
    write_rows(state/'data/hatexplain/canary.jsonl',canary)
    for model,pid in HX_POLICIES.items():
        policy=HX/'policies'/(pid+'.json')
        expected=read(HX/'freeze.json')['policy_hashes'][pid]
        if digest(policy)!=expected:raise ValueError('Frozen HateXplain policy changed')
        dest=state/'policies/hatexplain'/(pid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(policy,dest)
        policies['hatexplain/'+model]=dict(policy_id=pid,sha256=expected,**reg['models'][model])
        record(policy)
    records['hatexplain']=dict(official_train=len(divisions['train']),excluded_groups=len(excluded_groups),
        eligible=counts(eligible),fit=counts(fit),validation=counts(val),grouping=grouping,
        canary_rows=len(canary),canary_role='Earlier fitting rows, excluded from all ensemble fitting/selection; consistency diagnostic only')
    data_hashes={str(p.relative_to(state)):digest(p) for folder in ['data','scores'] for p in sorted((state/folder).rglob('*')) if p.is_file()}
    result=dict(created_utc=now(),seed=SEED,datasets=records,policies=policies,source_hashes=sources,data_hashes=data_hashes,
        hx_models=reg['models'],hx_settings=reg['settings'],protocol_sha256=digest(ROOT/'docs/ensemble/PLAN.md'))
    write(state/'data-manifest.json',result,exclusive=True)
    write(ROOT/'docs/ensemble/data-manifest.json',result)
    print({k:{s:v[s] for s in ['fit','validation']} for k,v in records.items()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--prior-work',required=True)
    prepare(**vars(p.parse_args()))
