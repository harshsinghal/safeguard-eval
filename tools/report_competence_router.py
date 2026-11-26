"""Package local prompt-free evidence and verify scores without model weights."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.routed_guard.common import ORDER, MODELS, ROOT, canonical, digest, rows, read, write, labels_for
from evals.competence_router.model import route, policy_contract_hash
from evals.competence_router.study import metrics, paired_interval


def load_rows(path):
    path=Path(path);b=path.read_bytes()
    if path.suffix=='.gz':b=gzip.decompress(b)
    return [json.loads(l) for l in b.decode().splitlines() if l.strip()]


def package(state,destination):
    from evals.competence_router.study import verify_freeze
    state=Path(state);destination=Path(destination);verify_freeze(state)
    if destination.exists():raise ValueError('Preserve existing evidence bundle')
    if not (state/'public/actual-results.json').exists():raise ValueError('Actual evaluation is incomplete')
    destination.mkdir(parents=True)
    for source in sorted((state/'public').rglob('*')):
        if not source.is_file():continue
        rel=source.relative_to(state/'public');target=destination/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.jsonl':
            target=Path(str(target)+'.gz');target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))
        else:shutil.copyfile(source,target)
    # Raw data, model weights, runtime paths, logs and credentials are never copied.
    manifest={str(p.relative_to(destination)):digest(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    write(destination/'manifest.json',dict(files=manifest,scope='Local prompt-free evidence; not published',models=MODELS))
    verify(destination)


def verify(bundle):
    bundle=Path(bundle);manifest=read(bundle/'manifest.json')
    for relative,h in manifest['files'].items():
        p=bundle/relative
        if not p.is_file() or digest(p)!=h:raise ValueError('Evidence hash mismatch: '+relative)
    required=['metadata/fit.jsonl.gz','metadata/validation.jsonl.gz','metadata/test.jsonl.gz','fit-targets.jsonl.gz',
        'test-routes.jsonl.gz','actual-routed.jsonl.gz','results.json','actual-results.json','selection-freeze.json']
    if any(not (bundle/p).exists() for p in required):raise ValueError('Missing required evidence')
    split_meta={s:load_rows(bundle/'metadata'/(s+'.jsonl.gz')) for s in ('fit','validation','test')}
    for a,aa in split_meta.items():
        for b,bb in split_meta.items():
            if a<b and {r['audit_group'] for r in aa}&{r['audit_group'] for r in bb}:raise ValueError('Cross-split audit groups')
    targets={r['id']:r for r in load_rows(bundle/'fit-targets.jsonl.gz')}
    for split,cases in split_meta.items():
        ids={c['id'] for c in cases};models={}
        for model in ORDER:
            rr=load_rows(bundle/'guards'/split/(model+'.jsonl.gz'));lookup={r['id']:r for r in rr}
            if len(rr)!=len(lookup) or set(lookup)!=ids:raise ValueError('Guard coverage mismatch')
            for c in cases:
                p=lookup[c['id']]
                if any(p.get(k)!=c[k] for k in ('input_sha256','policy_sha256','policy_id')) or p.get('model')!=model:raise ValueError('Unbound guard response')
                if p.get('status')=='ok':
                    if p.get('model_id')!=MODELS[model]['model'] or p.get('model_revision')!=MODELS[model]['revision'] or not p.get('full_input_passed'):raise ValueError('Native guard contract mismatch')
                if split=='fit':
                    t=targets[c['id']]['correctness'][model]
                    if t is not None and t!=int(p.get('status')=='ok' and p['prediction']==c['expected']):raise ValueError('Invalid competence target')
            models[model]=lookup
        if split!='test':continue
        plans=load_rows(bundle/'test-routes.jsonl.gz');plan={p['id']:p for p in plans}
        if len(plan)!=len(plans) or set(plan)!=ids:raise ValueError('Routing plan mismatch')
        selection=read(bundle/'validation-selection.json')['selected_route']['config']
        policies=read(ROOT/'benchmarks/enterprise-moderation/v0.1/policies.json')
        for c in cases:
            pp=plan[c['id']];q=[pp['correctness_probabilities'][m] for m in ORDER]
            model,_=route(q,selection,policy_contract_hash(policies[c['policy_id']],labels_for(c['policy_id'])))
            if model!=pp['selected_model']:raise ValueError('Recorded probabilities do not reproduce routing')
        fields=dict(clef=None,original_category='category_model',conservative_category='conservative_model',competence='selected_model')
        expected=read(bundle/'results.json')['test']['arms']
        for name,field in fields.items():
            outputs=[models['clef' if field is None else plan[c['id']][field]][c['id']] for c in cases]
            got=metrics(cases,outputs)
            for key in ('n','accuracy','available_task_macro_recall','tasks','confusion','successful_guard_coverage'):
                if got[key]!=expected[name][key]:raise ValueError('Score mismatch: '+name+'/'+key)
        actual=load_rows(bundle/'actual-routed.jsonl.gz');actual_by_id={r['id']:r for r in actual}
        if len(actual_by_id)!=len(actual) or set(actual_by_id)!=ids:raise ValueError('Actual request coverage mismatch')
        disagreements=0
        for c in cases:
            p=actual_by_id[c['id']];m=plan[c['id']]['selected_model']
            if not p.get('guard_attempted') or p.get('requested_model')!=m or not p.get('guard_attempts'):raise ValueError('Guard bypass or routing mismatch')
            if any(p.get(k)!=c[k] for k in ('input_sha256','policy_sha256','policy_id')):raise ValueError('Actual identity mismatch')
            if p['status']=='ok' and (p.get('model') not in ORDER or p.get('model_revision')!=MODELS[p['model']]['revision']):raise ValueError('Actual model version mismatch')
            disagreements+=p['prediction']!=models[m][c['id']]['prediction']
        got=metrics(cases,actual);expected_actual=read(bundle/'actual-results.json')
        if got['accuracy']!=expected_actual['accuracy'] or disagreements!=expected_actual['control_decision_changes']:raise ValueError('Actual result mismatch')
    public_stats={}
    for split in ('fit','validation','test','actual'):
        path=bundle/(split+'-device.jsonl.gz')
        if not path.exists():raise ValueError('Missing durable telemetry')
        rr=load_rows(path)
        if not rr:raise ValueError('Empty durable telemetry')
        public_stats[split]=dict(samples=len(rr),peak_temperature_c=max(r['temperature_c'] for r in rr),peak_power_w=max(r['power_w'] for r in rr))
    print(canonical(dict(verified=True,test_cases=len(split_meta['test']),actual_accuracy=read(bundle/'actual-results.json')['accuracy'],telemetry=public_stats)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['package','verify']);p.add_argument('--state');p.add_argument('--bundle',required=True)
    a=p.parse_args()
    if a.action=='package':package(a.state,a.bundle)
    else:verify(a.bundle)
