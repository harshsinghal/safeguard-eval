#!/usr/bin/env python3
"""Cross-check recorded test metrics with scikit-learn and direct error counts."""
import argparse, json, math
from pathlib import Path
from datetime import datetime, timezone
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, matthews_corrcoef

p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output')
args=p.parse_args();s=Path(args.run)
results=json.loads((s/'results.json').read_text())
selected=json.loads((s/'freeze.json').read_text())['selected']
assert set(results['tasks'])==set(selected)
checked=[]
for task, systems in results['tasks'].items():
    assert set(systems)==set(selected[task])
    expected={r['id']:r for r in map(json.loads,(s/f'metadata/{task}/test.jsonl').read_text().splitlines())}
    for model, row in systems.items():
        assert row['selected']==selected[task][model]
        if row['selected']=='brief':assert row['baseline']==row['metrics']
        arms={row['selected']:'metrics'}
        if row['baseline'] is not None and row['selected']!='brief':arms['brief']='baseline'
        for candidate, name in arms.items():
            records=[json.loads(x) for x in (s/f'predictions/{model}/{task}/test/{candidate}.jsonl').read_text().split('\n') if x]
            assert len(records)==len(expected) and {r['id'] for r in records}==set(expected)
            assert all(r['prompt_sha256']==expected[r['id']]['prompt_sha256'] and r['expected']==expected[r['id']]['expected'] for r in records)
            gold=[int(r['expected']=='BLOCK') for r in records]
            pred=[{'BLOCK':1,'ALLOW':0,'ERROR':-1}[r['prediction']] for r in records]
            n0=sum(y==0 for y in gold);n1=sum(y==1 for y in gold)
            fp=sum(y==0 and p==1 for y,p in zip(gold,pred))
            fn=sum(y==1 and p==0 for y,p in zip(gold,pred))
            tp=sum(y==1 and p==1 for y,p in zip(gold,pred))
            tn=sum(y==0 and p==0 for y,p in zip(gold,pred))
            unresolved=sum(p==-1 for p in pred)
            actual=dict(accuracy=accuracy_score(gold,pred),balanced_accuracy=balanced_accuracy_score(gold,pred),
                macro_f1=f1_score(gold,pred,labels=[0,1],average='macro',zero_division=0),
                mcc=matthews_corrcoef(gold,pred) if not unresolved else None,
                recall=tp/n1,specificity=tn/n0,false_blocks=fp,missed_violations=fn,unresolved=unresolved)
            for key,value in actual.items():
                claimed=row[name][key]
                assert (value is None and claimed is None) or (value is not None and claimed is not None and math.isclose(value,claimed,rel_tol=1e-12,abs_tol=1e-12)),(task,model,candidate,key,value,claimed)
            checked.append(dict(task=task,model=model,candidate=candidate,n=len(records),unresolved=unresolved,matches=True))
out=dict(created_utc=datetime.now(timezone.utc).isoformat(),method='Independent scikit-learn metrics and direct error counts; no study metric functions imported',
    coverage_alignment_verified=True,arms=checked,all_match=True)
if args.output:Path(args.output).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'verified_arms':len(checked),'all_match':True,'unresolved':sum(x['unresolved'] for x in checked)}))
