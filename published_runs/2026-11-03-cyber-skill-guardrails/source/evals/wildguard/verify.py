"""Verify complete final coverage and frozen identities before publication."""
import argparse
from collections import Counter
import json
from pathlib import Path

from evals.wildguard.run import digest,validate_freeze


def verify(root,freeze,test_provenance):
    root=Path(root);f=json.loads(Path(freeze).read_text());test=json.loads(Path(test_provenance).read_text())
    if test['freeze_sha256']!=digest(freeze):raise ValueError('Different test freeze')
    required={(a,p) for a,m in f['models'].items() for p in m['policy_ids']}
    required.add(('wildguard','wildguard-official'))
    expected_hash={'audit':f['audit_sha256'],'fit-final':f['final_fit_sha256'],'test':test['data_sha256']}
    seen={stage:set() for stage in expected_hash};counts=Counter();rows=Counter();populations={}
    for path in sorted(root.glob('*/summary.json')):
        m=json.loads(path.with_name('manifest.json').read_text());s=json.loads(path.read_text());stage=m['stage']
        if not s.get('complete') or s['n']!=len(m['ids']) or len(m['ids'])!=len(set(m['ids'])):raise ValueError('Incomplete or duplicate population')
        if m['policy_sha256'] is not None and digest(path.with_name('policy.json'))!=m['policy_sha256']:
            raise ValueError('Saved policy snapshot differs')
        counts[stage]+=1;rows[stage]+=s['n']
        if stage not in seen:continue
        key=(m['adapter'],m['policy_id'])
        if key in seen[stage]:raise ValueError('Repeated final configuration')
        seen[stage].add(key)
        validate_freeze(freeze,m['adapter'],m['policy_sha256'],m['revision'])
        if m['dataset_sha256']!=expected_hash[stage]:raise ValueError('Final dataset changed')
        if stage in populations and populations[stage]!=m['ids']:raise ValueError('Final populations differ')
        populations[stage]=m['ids']
        if m['runner_sha256']!=f['runner_sha256'] or m['legacy_adapter_sha256']!=f['legacy_adapter_sha256']:
            raise ValueError('Inference source differs')
        cap=8192 if m['adapter']=='safeguard' else 128 if m['adapter']=='wildguard' else 1
        if (m['max_tokens'],m['concurrency'],m['threshold'],m['temperature'])!=(cap,32,.5,0):raise ValueError('Final settings differ')
        if stage in ('audit','test') and m['freeze_sha256']!=digest(freeze):raise ValueError('Final run used different freeze')
    for stage,actual in seen.items():
        if actual!=required:raise ValueError('Missing frozen configurations in '+stage)
    return dict(complete=True,freeze_sha256=digest(freeze),runs_by_stage=dict(counts),
        predictions_by_stage=dict(rows),total_runs=sum(counts.values()),total_predictions=sum(rows.values()),
        unique_final_configurations=len(required),matched_final_populations=True,inference_sources_unchanged=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('runs','freeze','test-provenance','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();r=verify(a.runs,a.freeze,a.test_provenance);Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
