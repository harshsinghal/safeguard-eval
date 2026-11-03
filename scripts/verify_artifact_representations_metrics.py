#!/usr/bin/env python3
"""Independent count check for every new final arm, including neural seeds."""
import argparse
import json
from pathlib import Path
import math
from sklearn.metrics import balanced_accuracy_score, f1_score, matthews_corrcoef

def rows(p):return [json.loads(x) for x in p.read_text().split('\n') if x.strip()]

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();root=Path(a.run)
    freeze=json.loads((root/'freeze.json').read_text());results=json.loads((root/'results.json').read_text());count=0
    for task,models in freeze['selected'].items():
        metadata={r['id']:r for r in rows(root/f'metadata/{task}/test.jsonl')}
        for slug,best in models.items():
            pids=[f'{best}-s{s}' for s in (20261103,20261104,20261105)] if slug.endswith('-mlp') else [best]
            if slug.startswith('qwen'):pids=list(dict.fromkeys(pids+['brief']))
            for index,pid in enumerate(pids):
                rr=rows(root/f'predictions/{slug}/{task}/test/{pid}.jsonl')
                assert len(rr)==len(metadata) and {r['id'] for r in rr}==set(metadata)
                for r in rr:
                    assert all(r[k]==metadata[r['id']][k] for k in ('expected','group','prompt_sha256'))
                    assert math.isfinite(r['score']) and 0<=r['score']<=1
                    assert r['prediction']==('BLOCK' if r['score']>=.5 else 'ALLOW')
                y=[r['expected']=='BLOCK' for r in rr];pred=[r['prediction']=='BLOCK' for r in rr]
                fp=sum(not a and b for a,b in zip(y,pred));fn=sum(a and not b for a,b in zip(y,pred));n1=sum(y);n0=len(y)-n1
                expected=results['tasks'][task][slug]
                if slug.endswith('-mlp'):m=expected['seeds'][pid.rsplit('-s',1)[1]]
                elif index==0:m=expected['metrics']
                else:m=expected['baseline']
                assert m['false_blocks']==fp and m['missed_threats']==fn and m['unresolved']==0
                direct=.5*((n1-fn)/n1+(n0-fp)/n0)
                assert abs(direct-m['balanced_accuracy'])<1e-12
                for key,value in [('accuracy',1-(fp+fn)/len(y)),('balanced_accuracy',balanced_accuracy_score(y,pred)),
                    ('macro_f1',f1_score(y,pred,average='macro',zero_division=0)),('mcc',matthews_corrcoef(y,pred))]:
                    assert abs(float(value)-m[key])<1e-12,(task,slug,pid,key)
                count+=1
    print(f'Independently verified {count} final arms, all aligned and resolved.')

if __name__=='__main__':main()
