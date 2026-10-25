"""Recompute public Qwen and matched-policy comparisons without GPU access."""
import argparse
import json
from pathlib import Path

from evals.wildguard.reproduce import reproduce as reproduce_runs
from evals.qwen_policy.analyze import analyze


def reproduce(evidence,prior,out,intervals=False):
    evidence=Path(evidence);out=Path(out)
    result=reproduce_runs(evidence,out,intervals=False)
    if intervals:
        actual=analyze(out,evidence/'freeze.json',evidence/'selection.json',prior)
        if actual!=json.loads((evidence/'analysis.json').read_text()):raise ValueError('Paired analysis differs')
        (out/'analysis.json').write_text(json.dumps(actual,indent=2)+'\n')
    result['intervals_reproduced']=intervals
    (out/'reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('evidence','prior','out'):p.add_argument('--'+n,required=True)
    p.add_argument('--intervals',action='store_true');a=p.parse_args()
    print(json.dumps({k:v for k,v in reproduce(a.evidence,a.prior,a.out,a.intervals).items() if k!='runs'}))
