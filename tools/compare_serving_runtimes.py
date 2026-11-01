"""Compare the same saved requests across reference and optimized runtimes."""
import argparse
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.ensemble.common import read,write
from tools.report_serving import trace


def compare(reference,optimized,output):
    reference,optimized=Path(reference),Path(optimized);result={}
    for slug in read(optimized/'registration.json')['models']:
        directory=optimized/slug
        if not (directory/'complete.json').exists():
            result[slug]={'complete':False};continue
        comparisons=[]
        for path in sorted(directory.glob('measure-*.json')):
            previous=reference/slug/path.name
            if not previous.exists():continue
            a={r['id']:r for r in trace(previous.with_suffix('.jsonl'))}
            b=trace(path.with_suffix('.jsonl'))
            assert set(a)=={r['id'] for r in b}
            assert all(a[r['id']]['prompt_sha256']==r['prompt_sha256'] for r in b)
            deltas=[abs(r['score']-a[r['id']]['score']) for r in b]
            comparisons.append(dict(run=path.stem,n=len(b),
                decision_changes=sum(r['prediction']!=a[r['id']]['prediction'] for r in b),
                max_score_difference=max(deltas),median_score_difference=float(np.median(deltas)),
                throughput_ratio=read(path)['requests_per_second']/read(previous)['requests_per_second']))
        result[slug]=dict(complete=True,runs=comparisons)
    write(Path(output),result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--optimized',required=True);p.add_argument('--output',required=True)
    compare(**vars(p.parse_args()))
