"""Post-freeze descriptive checks on overlapping fitting evaluations."""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def read(path):
    return [json.loads(s) for s in Path(path).read_text().split('\n') if s.strip()]


def diagnostics(root):
    root=Path(root);runs={}
    for p in root.glob('*/summary.json'):
        m=json.loads(p.with_name('manifest.json').read_text())
        if m['stage'] in ('search','fit-final'):
            runs[(m['adapter'],m['policy_id'],m['stage'])]=(p.parent.name,m,read(p.with_name('predictions.jsonl')))
    entries=[]
    for (adapter,policy,stage),(name,m,rows) in sorted(runs.items()):
        if stage!='fit-final':continue
        earlier,original,old=runs[(adapter,policy,'search')]
        if m['revision']!=original['revision'] or m['policy_sha256']!=original['policy_sha256'] or m['runner_sha256']!=original['runner_sha256']:
            raise ValueError('Configuration changed')
        old={r['id']:r for r in old};shared=[r for r in rows if r['id'] in old]
        for r in shared:
            if any(r[k]!=old[r['id']][k] for k in ('expected','prompt_sha256','request_sha256')):
                raise ValueError('Repeated input differs')
        repeated=defaultdict(list)
        for r in rows:repeated[r['prompt_sha256']].append(r)
        groups=[v for v in repeated.values() if len(v)>1]
        entries.append(dict(adapter=adapter,policy_id=policy,expanded_run=name,search_run=earlier,
            shared_rows=len(shared),changed_predictions=sum(r['prediction']!=old[r['id']]['prediction'] for r in shared),
            corrected=sum(r['prediction']==r['expected'] and old[r['id']]['prediction']!=r['expected'] for r in shared),
            regressed=sum(r['prediction']!=r['expected'] and old[r['id']]['prediction']==r['expected'] for r in shared),
            repeated_exact_prompt_groups=len(groups),
            repeated_prompt_groups_with_different_predictions=sum(len({r['prediction'] for r in v})>1 for v in groups)))
    return dict(entries=entries,caveat='Exploratory consistency check, not a controlled repeatability experiment. Search and expanded fitting use different batch contexts. Temperature zero does not guarantee identical outputs.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();Path(a.out).write_text(json.dumps(diagnostics(a.runs),indent=2)+'\n')
