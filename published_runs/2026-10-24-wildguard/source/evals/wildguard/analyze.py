"""Paired reports from frozen prediction artifacts, without inspecting prompt text."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from evals.wildguard.metrics import report,paired_interval,metrics
from evals.wildguard.run import digest


def predictions(path):
    return [json.loads(x) for x in Path(path).read_text().split('\n') if x.strip()]


def analyze(root,freeze,overlap=None):
    root=Path(root);f=json.loads(Path(freeze).read_text());runs={};manifest={}
    selection_path=Path(freeze).with_name('selection.json')
    if digest(selection_path)!=f['selection_sha256']:raise ValueError('Selection differs from freeze')
    selection=json.loads(selection_path.read_text())
    for path in sorted(root.glob('*/summary.json')):
        m=json.loads(path.with_name('manifest.json').read_text())
        if m['split']!='test':continue
        rows=predictions(path.with_name('predictions.jsonl'))
        if len(rows)!=len(m['ids']) or len({r['id'] for r in rows})!=len(rows) or {r['id'] for r in rows}!=set(m['ids']):
            raise ValueError('Incomplete test run')
        if m['revision']!=f['models'][m['adapter']]['revision'] or m['policy_sha256'] not in f['models'][m['adapter']]['policy_hashes']:
            raise ValueError('Unregistered model/policy')
        if m['freeze_sha256']!=digest(freeze):raise ValueError('Different freeze')
        runs[path.parent.name]=rows;manifest[path.parent.name]=m
    baselines=[name for name,m in manifest.items() if m['adapter']=='wildguard']
    if len(baselines)!=1:raise ValueError('Exactly one WildGuard test baseline required')
    baseline=baselines[0];entries=[]
    # Require complete coverage of the registered unique configurations.
    required={(a,p) for a,m in f['models'].items() for p in m['policy_ids']}
    required.add(('wildguard','wildguard-official'))
    actual={(m['adapter'],m['policy_id']) for m in manifest.values()}
    if actual!=required or len(actual)!=len(runs):raise ValueError('Missing or duplicate frozen configurations')
    overlap_rows={}
    if overlap:
        o=json.loads(Path(overlap).read_text())
        if o['freeze_sha256']!=digest(freeze):raise ValueError('Different overlap freeze')
        overlap_rows={r['id']:r for r in o['rows']}
        if set(overlap_rows)!={r['id'] for r in runs[baseline]}:raise ValueError('Incomplete overlap audit')
    for name,rows in runs.items():
        m=manifest[name];initial=next((key for key,v in manifest.items() if v['adapter']==m['adapter'] and v['policy_id']=='wg-p0-taxonomy'),None)
        entry=dict(run=name,adapter=m['adapter'],policy_id=m['policy_id'],metrics=report(rows),
            vs_wildguard=paired_interval(rows,runs[baseline]),
            vs_initial=paired_interval(rows,runs[initial]) if initial else None)
        entry['roles']=['baseline'] if m['adapter']=='wildguard' else [role for role,policy in
            [('initial','wg-p0-taxonomy'),('shared',selection['shared']),('individual',selection['individual'][m['adapter']])]
            if m['policy_id']==policy]
        entry['annotator_agreement_slices']={str(v):metrics([r for r in rows if r.get('agreement')==v])
            for v in sorted({r.get('agreement') for r in rows},key=str)}
        if initial:
            initial_by_id={r['id']:r for r in runs[initial]}
            entry['failure_contribution_vs_initial']=dict(
                corrected_initial_errors=sum(initial_by_id[r['id']]['prediction']=='ERROR' and r['prediction']==r['expected'] for r in rows),
                lost_correct_to_new_errors=sum(initial_by_id[r['id']]['prediction']==r['expected'] and r['prediction']=='ERROR' for r in rows),
                initial_errors=sum(r['prediction']=='ERROR' for r in runs[initial]),
                final_errors=sum(r['prediction']=='ERROR' for r in rows))
        # Sensitivity: one source row per exact/near-duplicate test group, without relabeling.
        seen=set();unique=[]
        for r in rows:
            if r['group'] not in seen:unique.append(r);seen.add(r['group'])
        entry['deduplicated_first_row_sensitivity']=report(unique)
        if overlap_rows:
            clean=[r for r in rows if not overlap_rows[r['id']]['overlap']]
            clean_baseline=[r for r in runs[baseline] if not overlap_rows[r['id']]['overlap']]
            entry['no_detected_train_overlap_sensitivity']=dict(metrics=report(clean),vs_wildguard=paired_interval(clean,clean_baseline))
        entries.append(entry)
    controls=[];calibrated={}
    for control in f.get('calibration_thresholds',[]):
        name=next(k for k,m in manifest.items() if m['adapter']==control['adapter'] and m['policy_id']==control['policy_id'])
        rows=runs[name];threshold=control['threshold']
        rescored=[dict(r,prediction='ERROR' if r['prediction']=='ERROR' else 'BLOCK' if r['score']>=threshold else 'ALLOW') for r in rows]
        calibrated[(control['adapter'],control['policy_id'])]=rescored
        controls.append(dict(run=name,adapter=control['adapter'],policy_id=control['policy_id'],threshold=threshold,
            metrics=report(rescored),vs_fixed_threshold=paired_interval(rescored,rows),vs_wildguard=paired_interval(rescored,runs[baseline])))
    calibrated_comparisons=[]
    for adapter in ('policylm','shieldstral','cope'):
        policy_id=selection['individual'][adapter]
        initial=calibrated[(adapter,'wg-p0-taxonomy')];tuned=calibrated[(adapter,policy_id)]
        fixed=runs[next(k for k,m in manifest.items() if m['adapter']==adapter and m['policy_id']==policy_id)]
        calibrated_comparisons.append(dict(adapter=adapter,policy_id=policy_id,
            tuned_fixed_vs_calibrated_initial=paired_interval(fixed,initial),
            tuned_calibrated_vs_calibrated_initial=paired_interval(tuned,initial)))
    return dict(primary=f['primary'],baseline=baseline,entries=entries,calibration_controls=controls,
        calibrated_policy_comparisons=calibrated_comparisons,
        caveat='Shared and per-model winners may be the same policy. CIs are paired cluster bootstrap, conditional on the selected policies; no adjustment for multiple exploratory comparisons.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',required=True);p.add_argument('--freeze',required=True);p.add_argument('--out',required=True);p.add_argument('--overlap')
    a=p.parse_args();Path(a.out).write_text(json.dumps(analyze(a.runs,a.freeze,a.overlap),indent=2)+'\n')
