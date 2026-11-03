#!/usr/bin/env python3
"""Independent confusion-count and scikit-learn checks, including all controls."""
import argparse
import json
from pathlib import Path
from sklearn.metrics import balanced_accuracy_score, f1_score, matthews_corrcoef

def rows(p):return [json.loads(x) for x in p.read_text().split('\n') if x.strip()]

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();root=Path(a.run)
    result=json.loads((root/'results.json').read_text())['tasks']
    freeze=json.loads((root/'freeze.json').read_text())['selected'];count=0
    for task,models in freeze.items():
        meta={r['id']:r for r in rows(root/f'metadata/{task}/test.jsonl')}
        for slug,best in models.items():
            row=result[task]['models'][slug]
            primary=best+'-s20261104' if slug.endswith('-mlp') else best
            checks={primary:row['metrics']}
            if row.get('seeds'):
                checks.update({best+'-s'+s:m for s,m in row['seeds'].items()})
            if 'policy_vs_brief' in row:checks['brief']=row['policy_vs_brief']['reference_metrics']
            if 'full_vs_skill_only' in row:checks[best+'-md']=row['full_vs_skill_only']['reference_metrics']
            if 'custom_vs_default' in row:checks['default']=row['custom_vs_default']['reference_metrics']
            for pid,m in checks.items():
                rr=rows(root/f'predictions/{slug}/{task}/test/{pid}.jsonl')
                assert len(rr)==len(meta) and {r['id'] for r in rr}==set(meta)
                for r in rr:assert all(r[k]==meta[r['id']][k] for k in ('expected','group','prompt_sha256'))
                y=[r['expected']=='BLOCK' for r in rr];p=[r['prediction'] for r in rr]
                fp=sum(not a and b=='BLOCK' for a,b in zip(y,p));fn=sum(a and b=='ALLOW' for a,b in zip(y,p))
                tp=sum(a and b=='BLOCK' for a,b in zip(y,p));tn=sum(not a and b=='ALLOW' for a,b in zip(y,p))
                n1=sum(y);n0=len(y)-n1;errors=p.count('ERROR')
                assert (fp,fn,errors)==(m['false_blocks'],m['missed_violations'],m['unresolved'])
                assert abs(.5*(tp/n1+tn/n0)-m['balanced_accuracy'])<1e-12
                assert abs((tp+tn)/len(y)-m['accuracy'])<1e-12
                if not errors:
                    binary=[x=='BLOCK' for x in p]
                    for key,value in [('balanced_accuracy',balanced_accuracy_score(y,binary)),('macro_f1',f1_score(y,binary,average='macro',zero_division=0)),('mcc',matthews_corrcoef(y,binary))]:
                        assert abs(float(value)-m[key])<1e-12,(task,slug,pid,key)
                count+=1
    print(f'Independently verified {count} final arms and error denominators.')

if __name__=='__main__':main()
