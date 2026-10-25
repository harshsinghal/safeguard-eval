"""Compare frozen Qwen runs to immutable historical policy-model predictions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from evals.qwen_policy.run import SETTINGS,sources
from evals.wildguard.run import digest
from evals.wildguard.metrics import report,paired_interval

PAIRS={
    'Qwen/Qwen3.5-2B':['policylm'],
    'Qwen/Qwen3.5-4B':['shieldstral'],
    'Qwen/Qwen3.5-9B':['wildguard'],
    'Qwen/Qwen3.5-27B':['cope','safeguard'],
    'Qwen/Qwen3.5-35B-A3B':['cope','safeguard'],
}


def read(path):
    return [json.loads(x) for x in Path(path).read_text().split('\n') if x.strip()]


def historical(root):
    root=Path(root);runs={};manifest={}
    for item in json.loads((root/'run-index.json').read_text()):
        if item['stage']!='test':continue
        path=root/item['public_predictions'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['public_predictions_gzip_sha256']:raise ValueError('Historical artifact changed')
        rows=[json.loads(x) for x in gzip.decompress(raw).decode().split('\n') if x.strip()]
        runs[item['run']]=rows;manifest[item['run']]=json.loads(path.with_name('manifest.json').read_text())
        if len(rows)!=len(manifest[item['run']]['ids']):raise ValueError('Incomplete historical run')
    return runs,manifest,json.loads((root/'selection.json').read_text())


def threshold_rows(rows,t):
    return [dict(r,prediction='ERROR' if r['prediction']=='ERROR' else 'BLOCK' if r['score']>=t else 'ALLOW') for r in rows]


def analyze(root,freeze,selection,prior):
    root=Path(root);f=json.loads(Path(freeze).read_text());s=json.loads(Path(selection).read_text())
    if digest(selection)!=f['selection_sha256']:raise ValueError('Selection changed')
    old,old_manifest,old_selection=historical(prior);old_wg=old['wildguard-test-p0']
    required={(model,pid) for model,m in f['models'].items() for pid in m['policy_ids']}
    populations={};entries=[];pairs=[];controls=[];calibrated_pairs=[]
    for split in ('test','audit'):
        runs={};names={}
        for path in sorted(root.glob('*/summary.json')):
            m=json.loads(path.with_name('manifest.json').read_text())
            if m['split']!=split:continue
            key=(m['model'],m['policy_id']);rows=read(path.with_name('predictions.jsonl'))
            if key in runs or key not in required:raise ValueError('Duplicate or unregistered final configuration')
            if m['revision']!=f['models'][m['model']]['revision'] or m['policy_sha256'] not in f['models'][m['model']]['policy_hashes']:
                raise ValueError('Changed model or policy')
            if m['freeze_sha256']!=digest(freeze) or m['sources']!=f['sources'] or m['settings']!=f['settings']:
                raise ValueError('Changed frozen execution')
            if m['dataset_sha256']!=f['data_hashes'][split] or {r['split'] for r in rows}!={split}:
                raise ValueError('Changed final data')
            if len(rows)!=len(m['ids']) or {r['id'] for r in rows}!=set(m['ids']):raise ValueError('Incomplete rows')
            if digest(path.with_name('policy.json'))!=m['policy_sha256']:raise ValueError('Policy snapshot mismatch')
            summary=json.loads(path.read_text())
            if not summary.get('complete'):raise ValueError('Incomplete summary')
            for k,v in report(rows).items():
                if summary[k]!=v:raise ValueError('Metrics differ')
            runs[key]=rows;names[key]=path.parent.name
        if set(runs)!=required:raise ValueError('Missing final configurations: '+str(required-set(runs)))
        populations[split]=runs
        for (model,pid),rows in runs.items():
            roles=[role for role,p in [('initial','wg-p0-taxonomy'),('shared','wg-p2-boundary-checklist'),('selected',s['selected'][model])] if p==pid]
            entry=dict(run=names[(model,pid)],model=model,policy_id=pid,roles=roles,split=split,metrics=report(rows))
            if split=='test':
                entry['vs_initial']=paired_interval(rows,runs[(model,'wg-p0-taxonomy')])
                entry['vs_wildguard']=paired_interval(rows,old_wg)
            entries.append(entry)
    runs=populations['test']
    for model,comparators in PAIRS.items():
        for comparator in comparators:
            for role,pid in [('initial','wg-p0-taxonomy'),('shared','wg-p2-boundary-checklist'),('selected',s['selected'][model])]:
                prior_pid='wildguard-official' if comparator=='wildguard' else old_selection['individual'][comparator] if role=='selected' else pid
                name=next(n for n,m in old_manifest.items() if m['adapter']==comparator and m['policy_id']==prior_pid)
                qrows=runs[(model,pid)];orows=old[name]
                old_by_id={r['id']:r for r in orows}
                if any(r['prompt_sha256']!=old_by_id[r['id']]['prompt_sha256'] for r in qrows):raise ValueError('Different source prompts')
                pairs.append(dict(model=model,comparator=comparator,role=role,qwen_policy=pid,policy_model_run=name,
                    qwen_metrics=report(qrows),policy_model_metrics=report(orows),qwen_minus_policy=paired_interval(qrows,orows)))
    for c in f['controls']:
        if not c['available']:continue
        rows=runs[(c['model'],c['policy_id'])]
        if any(r['prediction']!='ERROR' and 'score' not in r for r in rows):
            controls.append(dict(model=c['model'],policy_id=c['policy_id'],available=False,reason='Incomplete valid-answer test scores'))
            continue
        t=c['selected']['threshold'];rescored=threshold_rows(rows,t)
        controls.append(dict(model=c['model'],policy_id=c['policy_id'],available=True,threshold=t,metrics=report(rescored),
            vs_free_generated=paired_interval(rescored,rows),vs_wildguard=paired_interval(rescored,old_wg)))
    old_controls={(c['adapter'],c['policy_id']):c['threshold'] for c in json.loads((Path(prior)/'freeze.json').read_text())['calibration_thresholds']}
    new_controls={(c['model'],c['policy_id']):c['threshold'] for c in controls if c['available']}
    for pair in pairs:
        key=(pair['model'],pair['qwen_policy'])
        if key not in new_controls:continue
        qrows=threshold_rows(runs[key],new_controls[key]);name=pair['policy_model_run'];m=old_manifest[name]
        old_threshold=old_controls.get((pair['comparator'],m['policy_id']))
        orows=old[name] if old_threshold is None else threshold_rows(old[name],old_threshold)
        calibrated_pairs.append(dict(model=pair['model'],comparator=pair['comparator'],role=pair['role'],
            qwen_threshold=new_controls[key],policy_model_threshold=old_threshold,
            policy_model_control='original explicit-label deployment' if old_threshold is None else 'previous validation-selected threshold',
            qwen_metrics=report(qrows),policy_model_metrics=report(orows),qwen_minus_policy=paired_interval(qrows,orows)))
    repeated=[]
    for model in f['models']:
        stages={}
        for path in sorted(root.glob('*/manifest.json')):
            m=json.loads(path.read_text())
            if m['model']==model and m['policy_id']=='wg-p0-taxonomy' and m['stage'] in ('pilot','search'):
                stages[m['stage']]={r['id']:r for r in read(path.with_name('predictions.jsonl'))}
        if set(stages)=={'pilot','search'}:
            a,b=stages['pilot'],stages['search'];common=a.keys()&b.keys()
            identical=[k for k in common if a[k]['request_sha256']==b[k]['request_sha256']]
            repeated.append(dict(model=model,common_rows=len(common),identical_request_rows=len(identical),
                changed_decisions=sum(a[k]['prediction']!=b[k]['prediction'] for k in identical),
                note='Descriptive repeated-input diagnostic under changed batch context, not a controlled repetition.'))
    return dict(exploratory=True,prior_test_results_known=True,entries=entries,paired_comparisons=pairs,calibration_controls=controls,
                calibrated_paired_comparisons=calibrated_pairs,repeatability=repeated,
                caveat='Nearby sizes and deployment choices are not controlled training-specialization ablations. All intervals are exploratory, unadjusted, conditional on selected prompts, and exclude runtime/annotation uncertainty.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('runs','freeze','selection','prior','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();Path(a.out).write_text(json.dumps(analyze(a.runs,a.freeze,a.selection,a.prior),indent=2)+'\n')
