"""Record prior-use exclusions; reserve unseen project groups before authoring."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import re
from pathlib import Path
from .common import ROOT,SEED,read,rows,write,write_rows,digest,now,assert_disjoint
from evals.wildguard.data import sample

ID_RE=re.compile(rb'wgtrain-\d{6}')
RAW_INVENTORY='published_runs/2026-10-24-wildguard/training-assignments.jsonl.gz'


def census(work):
    files=[]
    for folder in ['published_runs','docs','evals','research-preprint']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or str(p.relative_to(ROOT))==RAW_INVENTORY:continue
            if p.suffix in ('.json','.jsonl','.md','.txt') or p.name.endswith(('.json.gz','.jsonl.gz')):
                files.append(('repository/'+str(p.relative_to(ROOT)),p))
    # Local outputs include unsuccessful or not-yet-published predictions. Do not
    # equate a full prepared source pool with evaluated/instructive examples.
    skip={'env','.venv','venv','site-packages','vendor','node_modules','.git','__pycache__'}
    for project in sorted(work.glob('*-run')):
        if project.name=='policy-corrections-run':continue
        for p in project.rglob('*'):
            if not p.is_file() or any(x in skip for x in p.relative_to(project).parts):continue
            rel=p.relative_to(project)
            if (p.name.startswith('predictions.') or
                (('scores' in rel.parts or 'metadata' in rel.parts) and p.name.endswith(('.jsonl','.jsonl.gz'))) or
                ('features' in rel.parts and p.name=='records.json')):
                files.append(('work/'+str(p.relative_to(work)),p))
    used=set();records=[]
    for label,p in sorted(files):
        b=p.read_bytes();data=gzip.decompress(b) if p.suffix=='.gz' else b
        found={s.decode() for s in ID_RE.findall(data)}
        if found:
            used|=found
            records.append(dict(path=label,sha256=hashlib.sha256(b).hexdigest(),training_ids=len(found)))
    return used,records


def representatives(available,salt):
    groups=defaultdict(list)
    for r in available:groups[r['group']].append(r)
    return [min(rr,key=lambda r:hashlib.sha256(f'{SEED}:{salt}:{r["id"]}'.encode()).hexdigest())
            for _,rr in sorted(groups.items())]


def prepare(state,work):
    state,work=Path(state),Path(work)
    if (state/'data-manifest.json').exists():raise ValueError('Already prepared')
    prior=ROOT/'published_runs/2026-10-30-shield-probe'
    if digest(work/'wildguard-run/wildguard_train.parquet')!='02ecea8a724a9146a1e473a95a7cdf262adfe9c7d5408953ca86d2fcfbdc8953':raise ValueError('Wrong training source')
    if digest(work/'wildguard-run/test/wildguard_test.parquet')!='6ccc2909c1ae6d41424fac69f1fc32535b1de39cb8f80407d81e8bc64a0bebca':raise ValueError('Wrong test source')
    original=rows(work/'wildguard-run/data/train.jsonl');lookup={r['id']:r for r in original}
    import pyarrow.parquet as pq
    raw=pq.read_table(work/'wildguard-run/wildguard_train.parquet',columns=['prompt_harm_label']).column(0).to_pylist()
    assignments=rows(ROOT/RAW_INVENTORY)
    if len(original)!=86759 or len(assignments)!=86759:raise ValueError('Source population changed')
    aindex={r['id']:r for r in assignments}
    for r in original:
        a=aindex[r['id']]
        if any(r[k]!=a[k] for k in ['group','prompt_sha256','split']):raise ValueError('Assignment mismatch')
        if r['expected']!={'harmful':'BLOCK','unharmful':'ALLOW'}[raw[int(r['id'].split('-')[1])]]:raise ValueError('Label mismatch')
        if hashlib.sha256(r['prompt'].encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Source hash')
    used,records=census(work)
    unknown=used-set(lookup)
    if unknown:raise ValueError('Unknown prior IDs')
    groups=defaultdict(list)
    for r in original:groups[r['group']].append(r)
    used_groups={lookup[i]['group'] for i in used}
    overlaps=read(ROOT/'published_runs/2026-10-24-wildguard/train-test-overlap.json')
    overlap_ids={i for r in overlaps['rows'] for i in r['train_ids']}
    overlap_groups={lookup[i]['group'] for i in overlap_ids}
    conflicts={g for g,rr in groups.items() if len({r['expected'] for r in rr})>1}
    excluded=used_groups|overlap_groups|conflicts
    pools={s:representatives([r for r in original if r['split']==s and r['group'] not in excluded],s)
           for s in ['validation','audit']}
    if len(pools['validation'])<1536 or len(pools['audit'])<2048:raise ValueError('Insufficient unused groups')
    discovery_meta=rows(prior/'metadata/fit.jsonl.gz')
    populations={
        'discovery':[lookup[r['id']] for r in discovery_meta],
        'validation':sample(pools['validation'],1536,seed=SEED),
        'holdout':sample(pools['audit'],2048,seed=SEED+1),
    }
    test=rows(work/'policy-transfer-run/state/data/test.jsonl')
    frozen_test=rows(prior/'metadata/test.jsonl.gz')
    tindex={r['id']:r for r in test}
    populations['test']=[tindex[r['id']] for r in frozen_test]
    fields=['id','expected','group','prompt_sha256','subcategory','adversarial']
    for r in discovery_meta+frozen_test:
        actual=(lookup if r['id'].startswith('wgtrain-') else tindex)[r['id']]
        if any(r[k]!=actual[k] for k in fields):raise ValueError('Previous population changed')
    assert_disjoint(*populations.values())
    hashes={}
    for split,rr in populations.items():
        rr=sorted(rr,key=lambda r:r['id'])
        meta=[dict({k:r[k] for k in fields},split=split) for r in rr]
        inp=[{k:r[k] for k in ['id','prompt','prompt_sha256']} for r in rr]
        where='sealed-inputs' if split in ('holdout','test') else 'inputs'
        for rel,data in [('metadata/'+split+'.jsonl.gz',meta),(where+'/'+split+'.jsonl',inp)]:
            write_rows(state/rel,data);hashes[rel]=digest(state/rel)
    prior_scores=read(prior/'feature-provenance/shieldstral/fit/records.json')
    if [r['id'] for r in discovery_meta]!=[r['id'] for r in prior_scores]:raise ValueError('Discovery score order')
    errors=[]
    for m,s in zip(discovery_meta,prior_scores):
        if s['native_score'] is None:raise ValueError('No discovery score')
        predicted='BLOCK' if s['native_score']>=.5 else 'ALLOW'
        if predicted!=m['expected']:
            errors.append(dict(m,score=s['native_score'],prediction=predicted,
                error_type='false_block' if m['expected']=='ALLOW' else 'missed_violation'))
    write_rows(state/'discovery-errors.jsonl.gz',errors)
    write_rows(state/'private-discovery-errors.jsonl',[dict(e,prompt=lookup[e['id']]['prompt']) for e in errors])
    audit=dict(created_utc=now(),scanned_records=records,prior_used_ids=sorted(used),
        used_groups=sorted(used_groups),test_overlap_groups=sorted(overlap_groups),
        conflicting_groups=sorted(conflicts),excluded_groups=sorted(excluded),
        available_unique_groups={s:len(rr) for s,rr in pools.items()},
        raw_inventory_excluded_from_usage_census=dict(path=RAW_INVENTORY,sha256=digest(ROOT/RAW_INVENTORY),
            reason='Complete split assignments prepared before original experiments; not evidence every row was evaluated.'),
        limitation='Recorded prior use only; approximate lexical groups do not prove no semantic overlap or upstream training exposure.')
    write(state/'prior-use-audit.json',audit)
    write(state/'policies/p0.json',read(prior/'policy.json'))
    write(state/'discovery-summary.json',dict(n=len(discovery_meta),errors=len(errors),
        error_types=dict(Counter(e['error_type'] for e in errors)),
        error_categories=dict(Counter(e['subcategory'] for e in errors)),
        score_source=str((prior/'feature-provenance/shieldstral/fit/records.json').relative_to(ROOT)),
        score_sha256=digest(prior/'feature-provenance/shieldstral/fit/records.json'),cutoff=.5))
    hashes.update({p:digest(state/p) for p in ['prior-use-audit.json','discovery-errors.jsonl.gz','discovery-summary.json','policies/p0.json']})
    manifest=dict(created_utc=now(),counts={s:dict(n=len(rr),groups=len({r['group'] for r in rr}),
            labels=dict(Counter(r['expected'] for r in rr))) for s,rr in populations.items()},
        hashes=hashes,source_train_sha256=digest(work/'wildguard-run/wildguard_train.parquet'),
        source_test_sha256=digest(work/'wildguard-run/test/wildguard_test.parquet'),
        source_assignments_sha256=digest(ROOT/RAW_INVENTORY),seed=SEED,
        test_role='historical reused public test',holdout_role='previously unevaluated recorded project audit groups')
    write(state/'data-manifest.json',manifest,exclusive=True)
    print(json.dumps(dict(counts=manifest['counts'],prior_used_ids=len(used),
        excluded_groups=len(excluded),available=audit['available_unique_groups'],discovery=read(state/'discovery-summary.json')),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--work',required=True)
    prepare(**vars(p.parse_args()))
