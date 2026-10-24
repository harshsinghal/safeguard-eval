"""Paired reports from frozen prediction artifacts, without inspecting prompt text."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from evals.wildguard.metrics import report,paired_interval,calibrate


def predictions(path):
    return [json.loads(x) for x in Path(path).read_text().split('\n') if x.strip()]


def analyze(root,freeze):
    root=Path(root);f=json.loads(Path(freeze).read_text());runs={};manifest={}
    for path in sorted(root.glob('*/summary.json')):
        m=json.loads(path.with_name('manifest.json').read_text())
        if m['split']!='test':continue
        rows=predictions(path.with_name('predictions.jsonl'))
        if len(rows)!=len(m['ids']) or len({r['id'] for r in rows})!=len(rows) or {r['id'] for r in rows}!=set(m['ids']):
            raise ValueError('Incomplete test run')
        if m['revision']!=f['models'][m['adapter']]['revision'] or m['policy_sha256'] not in f['models'][m['adapter']]['policy_hashes']:
            raise ValueError('Unregistered model/policy')
        from evals.wildguard.run import digest
        if m['freeze_sha256']!=digest(freeze):raise ValueError('Different freeze')
        runs[path.parent.name]=rows;manifest[path.parent.name]=m
    baselines=[name for name,m in manifest.items() if m['adapter']=='wildguard']
    if len(baselines)!=1:raise ValueError('Exactly one WildGuard test baseline required')
    baseline=baselines[0];entries=[]
    for name,rows in runs.items():
        m=manifest[name];initial=next((key for key,v in manifest.items() if v['adapter']==m['adapter'] and v['policy_id']=='wg-p0-taxonomy'),None)
        entry=dict(run=name,adapter=m['adapter'],policy_id=m['policy_id'],metrics=report(rows),
            vs_wildguard=paired_interval(rows,runs[baseline]),
            vs_initial=paired_interval(rows,runs[initial]) if initial else None)
        # Sensitivity: one source row per exact/near-duplicate test group, without relabeling.
        seen=set();unique=[]
        for r in rows:
            if r['group'] not in seen:unique.append(r);seen.add(r['group'])
        entry['deduplicated_first_row_sensitivity']=report(unique)
        entries.append(entry)
    return dict(primary=f['primary'],baseline=baseline,entries=entries,
        caveat='Shared and per-model winners may be the same policy. CIs are paired cluster bootstrap, conditional on the selected policies; no adjustment for multiple exploratory comparisons.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',required=True);p.add_argument('--freeze',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();Path(a.out).write_text(json.dumps(analyze(a.runs,a.freeze),indent=2)+'\n')
