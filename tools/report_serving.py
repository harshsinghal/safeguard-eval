"""Recompute serving tables from per-request traces and timed pass durations."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.ensemble.common import read, rows, write
from evals.serving.client import summarize


def trace(path):
    path=Path(path)
    return rows(path if path.exists() else path.with_suffix(path.suffix+'.gz'))


def report(state, output):
    state=Path(state);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    registration=read(state/'registration.json');table=[];audit={}
    for slug,spec in registration['models'].items():
        directory=state/slug
        if not (directory/'complete.json').exists():
            audit[slug]=dict(complete=False);continue
        groups=defaultdict(list);baseline={r['id']:r for r in trace(directory/'measure-cache0-c1-r0.jsonl')}
        assert len(baseline)==registration['measurement_count']
        changes=[]
        for path in sorted(directory.glob('measure-*.json')):
            saved=read(path);records=trace(path.with_suffix('.jsonl'))
            assert len(records)==len(baseline) and {r['id'] for r in records}==set(baseline)
            assert all(r['prompt_sha256']==baseline[r['id']]['prompt_sha256'] for r in records)
            actual=summarize(records,saved['wall_seconds'])
            for key,value in actual.items():
                assert value==saved[key],(path,key)
            groups[(saved['cache'],saved['concurrency'])].append((saved,records))
            deltas=[abs(r['score']-baseline[r['id']]['score']) for r in records
                    if r.get('score') is not None and baseline[r['id']].get('score') is not None]
            changes.append(dict(run=path.stem,decision_changes=sum(r['prediction']!=baseline[r['id']]['prediction'] for r in records),
                max_score_difference=max(deltas,default=None),errors=saved['errors']))
        audit[slug]=dict(complete=True,reference='measure-cache0-c1-r0',runs=changes)
        historical=state/'historical'/(slug+'.jsonl')
        if historical.exists() or historical.with_suffix('.jsonl.gz').exists():
            old={r['id']:r for r in trace(historical)}
            matched=[r for k,r in baseline.items() if k in old]
            def old_label(r):
                if r.get('score') is not None and slug not in ('qwen-4b','wildguard'):
                    return 'BLOCK' if r['score']>=spec['threshold'] else 'ALLOW'
                return r['prediction']
            diffs=[abs(r['score']-old[r['id']]['score']) for r in matched if r.get('score') is not None and old[r['id']].get('score') is not None]
            audit[slug]['historical']=dict(matched=len(matched),decision_changes=sum(r['prediction']!=old_label(old[r['id']]) for r in matched),max_score_difference=max(diffs,default=None))
        for (cache,concurrency),runs in sorted(groups.items()):
            assert len(runs)==registration['repeats']
            all_records=[r for _,rr in runs for r in rr]
            total=summarize(all_records,sum(s['wall_seconds'] for s,_ in runs))
            batches=[r['batch_size'] for r in all_records if 'batch_size' in r]
            tokens=[r.get('input_tokens',r.get('usage',{}).get('prompt_tokens')) for r in all_records]
            tokens=[t for t in tokens if t is not None]
            outtokens=[r.get('usage',{}).get('completion_tokens') for r in all_records]
            outtokens=[t for t in outtokens if t is not None]
            table.append(dict(model=slug,backend=spec['backend'],cache=cache,concurrency=concurrency,
                **total,repeat_rate_min=min(s['requests_per_second'] for s,_ in runs),
                repeat_rate_max=max(s['requests_per_second'] for s,_ in runs),
                mean_actual_batch=float(np.mean(batches)) if batches else None,
                input_tokens_median=float(np.median(tokens)) if tokens else None,
                input_tokens_p95=float(np.quantile(tokens,.95)) if tokens else None,
                output_tokens_median=float(np.median(outtokens)) if outtokens else None))
    write(output/'summary.json',table);write(output/'repeat-parity.json',audit)
    if table:
        with (output/'results.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    for slug in registration['models']:
        rr=[r for r in table if r['model']==slug and not r['cache']]
        if not rr:continue
        single=next(r for r in rr if r['concurrency']==1);best=max(rr,key=lambda r:r['requests_per_second'])
        print(f"{slug:12s} {single['backend']:6s} single {single['p50_ms']:.1f}ms p95 {single['p95_ms']:.1f}ms; loaded C{best['concurrency']} {best['requests_per_second']:.1f}/s p95 {best['p95_ms']:.1f}ms ${best['gpu_usd_per_million']:.2f}/M")
    return table


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();report(a.state,a.output)
