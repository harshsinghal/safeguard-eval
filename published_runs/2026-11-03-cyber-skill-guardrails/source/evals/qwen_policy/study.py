"""Validate matched candidate runs, select on validation and freeze the follow-up."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from evals.qwen_policy.run import SETTINGS,sources
from evals.wildguard.run import digest
from evals.wildguard.metrics import metrics,calibrate


def load_run(path,split,model,policy_hash,revision,data_hash):
    p=Path(path);m=json.loads((p/'manifest.json').read_text())
    rows=[json.loads(line) for line in (p/'predictions.jsonl').read_text().split('\n') if line.strip()]
    expected=dict(split=split,model=model,revision=revision,policy_sha256=policy_hash,
                  dataset_sha256=data_hash,settings=SETTINGS,sources=sources())
    if any(m.get(k)!=v for k,v in expected.items()):raise ValueError('Changed run identity: '+p.name)
    if len(rows)!=len(m['ids']) or {r['id'] for r in rows}!=set(m['ids']):raise ValueError('Incomplete run')
    if {r['split'] for r in rows}!={split}:raise ValueError('Wrong partition')
    summary=json.loads((p/'summary.json').read_text())
    if not summary.get('complete'):raise ValueError('Incomplete summary')
    for k,v in metrics(rows).items():
        if v!=summary[k]:raise ValueError('Metric mismatch')
    return m,rows


def select(registry,runs):
    registry=Path(registry);r=json.loads(registry.read_text());records=[];ids={}
    for c in r['candidates']:
        policy_path=registry.parent/c['path']
        if digest(policy_path)!=c['sha256']:raise ValueError('Candidate changed')
        policy=json.loads(policy_path.read_text());scores={};paths={}
        for split in ('fit','validation'):
            name=c['runs'][split];paths[split]=name
            m,rows=load_run(Path(runs)/name,split,c['model'],c['sha256'],r['models'][c['model']]['revision'],r['data_hashes'][split])
            if split in ids and ids[split]!=m['ids']:raise ValueError('Different candidate populations')
            ids[split]=m['ids'];scores[split]=metrics(rows)
        records.append(dict(model=c['model'],policy_id=policy['id'],policy_sha256=c['sha256'],path=c['path'],
                            words=len(' '.join(str(v) for v in policy.values()).split()),scores=scores,runs=paths))
    selected={}
    for model in r['models']:
        candidates=[v for v in records if v['model']==model]
        if len(candidates)!=5:raise ValueError('Expected five candidates per model')
        selected[model]=sorted(candidates,key=lambda v:(-v['scores']['validation']['accuracy'],v['words'],v['policy_id']))[0]['policy_id']
    return dict(created_utc=datetime.now(timezone.utc).isoformat(),registry_sha256=digest(registry),
                objective='validation accuracy; shorter text then lexicographic ID',selected=selected,records=records,
                exploratory=True,prior_official_test_results_known=True)


def freeze(registry,selection,runs,out):
    if Path(out).exists():raise ValueError('Freeze exists')
    registry=Path(registry);r=json.loads(registry.read_text());s=json.loads(Path(selection).read_text())
    if s['registry_sha256']!=digest(registry):raise ValueError('Registry changed')
    models={};controls=[]
    for model,meta in r['models'].items():
        ids={'wg-p0-taxonomy','wg-p2-boundary-checklist',s['selected'][model]}
        records=[v for v in s['records'] if v['model']==model and v['policy_id'] in ids]
        if {v['policy_id'] for v in records}!=ids:raise ValueError('Missing final policy')
        models[model]=dict(revision=meta['revision'],policy_ids=sorted(ids),policy_hashes=sorted(v['policy_sha256'] for v in records))
        for record in records:
            _,rows=load_run(Path(runs)/record['runs']['validation'],'validation',model,record['policy_sha256'],meta['revision'],r['data_hashes']['validation'])
            base=dict(model=model,policy_id=record['policy_id'],policy_sha256=record['policy_sha256'])
            try:control=calibrate(rows)
            except ValueError:controls.append(dict(**base,available=False,reason='Incomplete valid-answer score coverage'))
            else:controls.append(dict(**base,available=True,**control))
    f=dict(status='frozen',created_utc=datetime.now(timezone.utc).isoformat(),models=models,
           registry_sha256=digest(registry),selection_sha256=digest(selection),settings=SETTINGS,sources=sources(),
           data_hashes=r['data_hashes'],dataset=r['dataset'],controls=controls,
           prior_official_test_results_known=True,new_qwen_test_inference_started=False,policy_editing_closed=True)
    Path(out).write_text(json.dumps(f,indent=2)+'\n');return f


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('select','freeze'))
    for n in ('registry','runs','out'):p.add_argument('--'+n,required=True)
    p.add_argument('--selection');a=p.parse_args()
    if a.command=='select':
        if Path(a.out).exists():raise ValueError('Selection exists')
        Path(a.out).write_text(json.dumps(select(a.registry,a.runs),indent=2)+'\n')
    else:freeze(a.registry,a.selection,a.runs,a.out)
