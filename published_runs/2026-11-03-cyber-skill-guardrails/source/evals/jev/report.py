"""Export and reproduce a prompt-free Jev prediction archive without API calls."""
import argparse
from collections import defaultdict
import copy
import gzip
import json
import math
from pathlib import Path
import shutil
import statistics

from evals.ensemble.common import digest, read, rows, write_rows
from evals.jev.api import parse, save, billed_cost, canonical, hash_value
from evals.jev.study import ROOT, DATA, IDS, predictions, verify_freeze, select_policy, select_threshold, threshold_rows
from evals.wildguard.metrics import metrics, paired_interval


def summarize(rr):
    m=metrics(rr)
    cm=m['confusion']; tp=cm['BLOCK']['BLOCK']; fp=cm['ALLOW']['BLOCK']
    m['false_blocks']=fp
    m['missed_violations']=cm['BLOCK']['ALLOW']
    m['block_precision']=tp/(tp+fp) if tp+fp else 0.
    if all(isinstance(r.get('score'),(int,float)) and r['prediction']!='ERROR' for r in rr):
        ss=[(min(max(r['score'],1e-7),1-1e-7),int(r['expected']=='BLOCK')) for r in rr]
        m['brier']=sum((s-y)**2 for s,y in ss)/len(ss)
        m['log_loss']=-sum(y*math.log(s)+(1-y)*math.log(1-s) for s,y in ss)/len(ss)
    return m


def align(reference, target):
    index={r['id']:r for r in target}
    if len(index)!=len(target) or len(reference)!=len(target) or {r['id'] for r in reference}!=set(index):
        raise ValueError('Comparison populations differ')
    out=[]
    for r in reference:
        t=index[r['id']]
        if any(r[k]!=t[k] for k in ('expected','prompt_sha256')):
            raise ValueError('Comparison content or gold labels differ')
        # Both sides use the current frozen test's duplicate grouping for bootstrap.
        out.append(dict(r,group=t['group']))
    return sorted(out,key=lambda r:r['id'])


def references(dataset):
    found={}; provenance={}
    def add(name,path,candidate=None):
        rr=rows(path)
        if candidate is not None:rr=[r for r in rr if r.get('candidate')==candidate]
        if not rr:raise ValueError('Missing frozen comparison '+name)
        found[name]=rr
        provenance[name]=dict(path=str(path.relative_to(ROOT)),sha256=digest(path),candidate=candidate)
    if dataset=='wildguard':
        add('WildGuard-7B',ROOT/'published_runs/2026-10-24-wildguard/runs/wildguard-test-p0/predictions.jsonl.gz')
    cohort='wildguard-specialists' if dataset=='wildguard' else 'hatexplain-specialists'
    root=ROOT/'published_runs/2026-10-28-ensemble-logits/cohorts'
    for c in ([cohort] if dataset=='wildguard' else [cohort,'hatexplain-mixed']):
        selection=read(root/c/'selection.json')['selected']
        for model,candidate in selection['per_model'].items():
            name=model+' calibrated'
            if name in found:continue
            path=root/c/'test-predictions.jsonl.gz'
            # Reused probability calibrators live in the previous evidence bundle.
            if not candidate.startswith('logit-'):
                path=ROOT/'published_runs/2026-10-27-ensemble/cohorts'/c/'test-predictions.jsonl.gz'
            add(name,path,candidate)
        name='Log-odds ensemble ('+('specialists + Qwen' if c.endswith('mixed') else 'specialists')+')'
        add(name,root/c/'test-predictions.jsonl.gz',selection['primary'])
    return found,provenance


def public_policy_record(dataset, policies, examples):
    """Keep gated WildGuard demonstration text in the private run directory."""
    public=copy.deepcopy(policies)
    info={pid:dict(original_question_sha256=hash_value(q),serialized_bytes=len(canonical(q).encode()))
          for pid,q in policies.items()}
    if dataset=='wildguard':
        public['examples']['instructions']=public['detailed']['instructions'] + (
            '\n\n[Four licensed training examples withheld from the public archive. '
            'Reconstruct from examples-provenance.json and the pinned training dataset. '
            'This redacted question is not the request used for inference.]')
        info['examples']['redacted']=True
    provenance=[{k:v for k,v in r.items() if k!='prompt'} for r in examples]
    return public,info,provenance


def archive_selection(questions, prediction_sets, interface):
    """Use recorded original byte counts for a tie involving a redacted question."""
    if set(prediction_sets)!=set(IDS) or set(questions)!=set(IDS):raise ValueError('Missing policies')
    for rr in prediction_sets.values():
        if {r['split'] for r in rr}!={'validation'}:raise ValueError('Selection is validation-only')
    for pid,q in questions.items():
        i=interface[pid]
        if not i.get('redacted') and (hash_value(q)!=i['original_question_sha256'] or len(canonical(q).encode())!=i['serialized_bytes']):
            raise ValueError('Policy interface does not match saved identity')
    summaries={pid:metrics(rr) for pid,rr in prediction_sets.items()}
    chosen=min(IDS,key=lambda pid:(-summaries[pid]['accuracy'],-summaries[pid]['macro_f1'],interface[pid]['serialized_bytes'],pid))
    return chosen,summaries


def export(state,destination):
    state,destination=Path(state),Path(destination)
    verify_freeze(state)
    if destination.exists():raise ValueError('Evidence destination already exists')
    destination.mkdir(parents=True)
    def copy(source,rel):
        p=destination/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,p)
    for name in ['registration.json','policies-freeze.json','freeze.json','PLAN.md','connectivity.json','costs.json']:
        copy(state/name,name)
    reference_manifest={}
    for dataset in DATA:
        original=read(state/'policies'/dataset/'final.json')
        examples=read(state/'policies'/dataset/'examples-provenance.json')
        public,interface,provenance=public_policy_record(dataset,original,examples)
        save(destination/'policies'/dataset/'final.json',public)
        save(destination/'policies'/dataset/'interface.json',interface)
        save(destination/'policies'/dataset/'examples-provenance.json',provenance)
        copy(state/'policies'/dataset/'initial.json',Path('policies')/dataset/'initial.json')
        for split in ['fit','validation','test']:
            for pid in (['brief','detailed'] if split=='fit' else IDS):
                rr=predictions(state,dataset,split,pid)
                write_rows(destination/'predictions'/dataset/split/(pid+'.jsonl.gz'),rr)
            raw=[]
            for p in sorted((state/'runs'/dataset/split/'raw').glob('*.json')):
                if len(p.stem)==64:
                    raw.append(read(p))
            if len(raw)!=DATA[dataset][split][1]:raise ValueError('Raw response population incomplete')
            write_rows(destination/'responses'/dataset/(split+'.jsonl.gz'),raw)
        target=predictions(state,dataset,'test','brief')
        refs,provenance=references(dataset)
        reference_manifest[dataset]=provenance
        for i,(name,rr) in enumerate(refs.items()):
            aligned=align(rr,target)
            rel=Path('references')/dataset/(str(i)+'.jsonl.gz')
            write_rows(destination/rel,aligned)
            provenance[name]['evidence_path']=str(rel)
    save(destination/'references.json',reference_manifest)
    for rel in ['evals/__init__.py','evals/ensemble/__init__.py','evals/ensemble/common.py',
                'evals/wildguard/__init__.py','evals/wildguard/metrics.py',
                'evals/jev/__init__.py','evals/jev/api.py','evals/jev/study.py','evals/jev/report.py']:
        copy(ROOT/rel,Path('source')/rel)
    copy(ROOT/'tests/test_jev.py','source/tests/test_jev.py')
    checksums(destination)


def checksums(bundle):
    bundle=Path(bundle)
    save(bundle/'checksums.json',{str(p.relative_to(bundle)):digest(p) for p in sorted(bundle.rglob('*'))
        if p.is_file() and p.name not in ('checksums.json','reproduction.json') and '__pycache__' not in p.parts})


def verify_bundle(bundle):
    for rel,h in read(Path(bundle)/'checksums.json').items():
        if digest(Path(bundle)/rel)!=h:raise ValueError('Changed evidence: '+rel)


def analyze(bundle):
    bundle=Path(bundle)
    verify_bundle(bundle)
    frozen=read(bundle/'freeze.json')
    result=dict(model='typesafe/jev-1.14-20261014',datasets={})
    latency=[]; costs=[]; question_count=0
    for dataset in DATA:
        pp=read(bundle/'policies'/dataset/'final.json')
        by_split={}
        for split in ['fit','validation','test']:
            pids=['brief','detailed'] if split=='fit' else IDS
            rr={pid:rows(bundle/'predictions'/dataset/split/(pid+'.jsonl.gz')) for pid in pids}
            raw=rows(bundle/'responses'/dataset/(split+'.jsonl.gz'))
            raw_index={r['id']:r for r in raw}
            if len(raw_index)!=len(raw) or len(raw)!=DATA[dataset][split][1]:
                raise ValueError('Invalid raw response population')
            for pid,pred in rr.items():
                if len(pred)!=len(raw) or {r['id'] for r in pred}!=set(raw_index):raise ValueError('Missing rows')
                for r in pred:
                    a=raw_index[r['id']]
                    parsed=parse(a['response'],pids)[pid]
                    if any(r[k]!=parsed[k] for k in ('prediction','score','confidence','probabilities')):
                        raise ValueError('Predictions disagree with native API response')
                    if r['request_sha256']!=a['request_sha256']:raise ValueError('Request mismatch')
            latency.extend(r['latency_seconds'] for r in raw)
            costs.extend(billed_cost(r['response']) for r in raw)
            question_count+=len(raw)*len(pids)
            by_split[split]=rr
        chosen,vm=archive_selection(pp,by_split['validation'],read(bundle/'policies'/dataset/'interface.json'))
        f=frozen['selections'][dataset]
        if chosen!=f['policy'] or vm!=f['native_validation']:raise ValueError('Selection does not reproduce')
        thresholds={pid:select_threshold(by_split['validation'][pid]) for pid in sorted({'brief',chosen})}
        if thresholds!=f['thresholds']:raise ValueError('Thresholds do not reproduce')
        test=by_split['test']
        arms={pid+'/default':rr for pid,rr in test.items()}
        arms['brief/calibrated']=threshold_rows(test['brief'],thresholds['brief']['selected']['threshold'])
        arms['selected/default']=test[chosen]
        arms['selected/calibrated']=threshold_rows(test[chosen],thresholds[chosen]['selected']['threshold'])
        primary=arms['selected/calibrated']
        refs={name:align(rows(bundle/info['evidence_path']),primary)
              for name,info in read(bundle/'references.json')[dataset].items()}
        comparisons={'brief/default':paired_interval(primary,arms['brief/default'],reps=2000,seed=20261029)}
        for name,rr in refs.items():
            comparisons[name]=paired_interval(primary,rr,reps=2000,seed=20261029)
        # Added descriptive attribution intervals after the first results inspection;
        # no policy, threshold, input, or inference was changed.
        adaptation={
            'policy_at_native_choice':paired_interval(arms['selected/default'],arms['brief/default'],reps=2000,seed=20261029),
            'threshold_on_selected_policy':paired_interval(primary,arms['selected/default'],reps=2000,seed=20261029),
            'selected_vs_brief_both_threshold_tuned':paired_interval(primary,arms['brief/calibrated'],reps=2000,seed=20261029)}
        slices={}
        for field in (['adversarial','subcategory'] if dataset=='wildguard' else ['source_label','platform','agreement']):
            slices[field]={str(v):summarize([r for r in primary if r.get(field)==v])
                           for v in sorted({r.get(field) for r in primary},key=str)}
        result['datasets'][dataset]=dict(selected_policy=chosen,
            thresholds={pid:t['selected']['threshold'] for pid,t in thresholds.items()},
            fitting={pid:summarize(rr) for pid,rr in by_split['fit'].items()},
            validation=vm,test={name:summarize(rr) for name,rr in arms.items()},
            references={name:summarize(rr) for name,rr in refs.items()},comparisons=comparisons,
            adaptation_comparisons=adaptation,slices=slices)
    initial=read(bundle/'connectivity.json')['response']['usage']['cost']
    measured=sum(costs)+initial
    accounting=read(bundle/'costs.json')
    # This reproduction currently expects all paid benchmark attempts succeeded.
    # If errors/retries occurred, require a billing-aware extension before claiming exact reconciliation.
    if set(accounting['statuses'])!={'reported'} or abs(measured-accounting['total_accounted_usd'])>1e-9:
        raise ValueError('Billing cannot be reconciled solely from successful responses')
    latency.sort()
    result['usage']=dict(benchmark_requests=len(costs),benchmark_classifications=question_count,
        connectivity_requests=1,actual_cost_usd=measured,cap_usd=accounting['cap_usd'],
        latency_median_seconds=statistics.median(latency),latency_p95_seconds=latency[int(.95*(len(latency)-1))],
        latency_note='Client-observed requests with two or three independent policy questions, concurrency up to eight; not a matched serving benchmark.')
    return result


def markdown(result):
    lines=['# Jev 1.14: complete benchmark results','',
        'Policies and thresholds were selected on validation before test inference. '
        'These are reused public test sets, so comparisons are exploratory. '
        'All tasks are binary ALLOW/BLOCK; no REVIEW label was evaluated.','',
        'For Jev, `/calibrated` means only that the classification threshold was chosen '
        'on validation. Its probabilities were not transformed and no calibration model '
        'was fitted. The historical individual controls used learned score calibrators.','']
    for dataset,d in result['datasets'].items():
        lines+=['## '+dataset,'',f"Validation-selected policy: **{d['selected_policy']}**. Thresholds: `{d['thresholds']}`.",'',
            '| Configuration | Accuracy | Macro-F1 | BLOCK recall | False blocks | Missed violations |',
            '|---|---:|---:|---:|---:|---:|']
        for name,m in list(d['test'].items())+list(d['references'].items()):
            lines.append(f"| {name} | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% | {100*m['harmful_recall']:.2f}% | {m['false_blocks']} | {m['missed_violations']} |")
        lines+=['','### Validation policy comparison','',
            '| Policy | Accuracy | Macro-F1 |','|---|---:|---:|']
        for name,m in d['validation'].items():lines.append(f"| {name} | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% |")
        lines+=['','### Selected/calibrated Jev minus each reference','',
            '| Reference | Accuracy difference (points) | 95% paired interval | Cases fixed | Cases broken |',
            '|---|---:|---:|---:|---:|']
        for name,c in d['comparisons'].items():
            lines.append(f"| {name} | {100*c['delta']:+.2f} | {100*c['ci95'][0]:+.2f} to {100*c['ci95'][1]:+.2f} | {c['a_correct_b_wrong']} | {c['a_wrong_b_correct']} |")
        lines+=['','### Separating wording from thresholds','',
            'These additional descriptive intervals were computed after inspecting the '
            'initial results. No test-based optimization or extra inference followed.','',
            '| Comparison | Accuracy difference (points) | 95% paired interval |',
            '|---|---:|---:|']
        for name,c in d['adaptation_comparisons'].items():
            lines.append(f"| {name} | {100*c['delta']:+.2f} | {100*c['ci95'][0]:+.2f} to {100*c['ci95'][1]:+.2f} |")
        lines+=['','Intervals use 2,000 paired duplicate-group bootstrap draws and are unadjusted. '
            'Historical references used different development budgets and sometimes trained calibrators or ensembles; '
            'these comparisons do not isolate architecture. Full confusion matrices, calibration metrics, '
            'and content slices are in results.json.','']
    u=result['usage']
    lines+=['## Usage','',f"{u['benchmark_requests']:,} benchmark requests; {u['benchmark_classifications']:,} classifications; one separate synthetic connectivity request. "
        f"Actual API charge: **${u['actual_cost_usd']:.6f}**, within the ${u['cap_usd']:.2f} ceiling. No GPU rental.",'',
        f"Median request latency {u['latency_median_seconds']:.3f}s; p95 {u['latency_p95_seconds']:.3f}s. {u['latency_note']}",'']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['export','analyze','reproduce'])
    p.add_argument('--state',type=Path)
    p.add_argument('--bundle',type=Path,required=True)
    a=p.parse_args()
    if a.command=='export':export(a.state,a.bundle)
    else:
        result=analyze(a.bundle)
        if a.command=='reproduce':
            if result!=read(a.bundle/'results.json'):raise ValueError('Results did not reproduce exactly')
            save(a.bundle/'reproduction.json',dict(status='passed',metrics_and_selections='exact',
                paid_api_calls=0,cost_usd=0,benchmark_rows=sum(DATA[d]['test'][1] for d in DATA)))
            print('Reproduced metrics, validation choices, paired intervals and API billing exactly; no paid calls.')
        else:
            save(a.bundle/'results.json',result)
            (a.bundle/'RESULTS.md').write_text(markdown(result))
            checksums(a.bundle)
            print(json.dumps({d:{k:v['accuracy'] for k,v in r['test'].items()} for d,r in result['datasets'].items()},indent=2))
            print(result['usage'])


if __name__=='__main__':main()
