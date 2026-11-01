"""Recompute length curves and engine output consistency from public traces."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals.serving.cloud_lengths import rows, summary, write


def report(root):
    def mean_or_none(values):
        return statistics.mean(values) if all(v is not None for v in values) else None
    result = dict(engines={}, cross_engine=None)
    for engine in ('vllm','sglang'):
        d = root/engine
        if not (d/'freeze.json').exists():
            result['engines'][engine] = dict(status='no accepted selection')
            continue
        freeze = json.loads((d/'freeze.json').read_text())
        selected = freeze['selected']['parameter']
        assert selected == max(freeze['candidates'],key=lambda r:r['requests_per_second'])['parameter']
        curves = []
        for group in ('64','256','1024','4096','mixed'):
            for concurrency in (1,8,32):
                repetitions = []
                for repeat in (0,1):
                    p = d/f'measure-{group}-c{concurrency}-r{repeat}'
                    if not p.with_suffix('.json').exists(): continue
                    saved = json.loads(p.with_suffix('.json').read_text())
                    records = rows(p.with_suffix('.jsonl'))
                    recomputed = summary(records, saved['wall_seconds'])
                    for key in ('requests','valid','errors','requests_per_second','p50_ms','p95_ms',
                                'gpu_usd_per_million','prompt_tokens','completion_tokens'):
                        assert recomputed[key]==saved[key], (p,key)
                    assert len(records)==64 and len({r['id'] for r in records})==64
                    assert all(r['usage']['prompt_tokens']==r['full_tokens']
                               for r in records if r['prediction']!='ERROR')
                    repetitions.append(dict(repeat=repeat, **saved))
                if len(repetitions)!=2: continue
                curves.append(dict(content_tokens=group, concurrency=concurrency,
                    requests=sum(r['requests'] for r in repetitions),
                    errors=sum(r['errors'] for r in repetitions),
                    requests_per_second=statistics.mean(r['requests_per_second'] for r in repetitions),
                    p50_ms=mean_or_none([r['p50_ms'] for r in repetitions]),
                    p95_ms=mean_or_none([r['p95_ms'] for r in repetitions]),
                    gpu_usd_per_million=mean_or_none([r['gpu_usd_per_million'] for r in repetitions]),
                    repeats=repetitions))
        result['engines'][engine] = dict(status='complete' if len(curves)==15 else 'partial',
            parameter=selected, curves=curves)
    gates = {}
    for engine in ('vllm','sglang'):
        spec = result['engines'][engine]
        if 'parameter' in spec:
            gates[engine] = {r['id']:r for r in rows(root/engine/f"parity-p{spec['parameter']}.jsonl")}
    if len(gates)==2:
        a,b = gates['vllm'],gates['sglang']
        assert set(a)==set(b) and len(a)==32
        assert all(a[i]['input_sha256']==b[i]['input_sha256'] for i in a)
        result['cross_engine'] = dict(fitting_n=32,
            label_differences=sum(a[i]['prediction']!=b[i]['prediction'] for i in a),
            errors=sum(a[i]['prediction']=='ERROR' or b[i]['prediction']=='ERROR' for i in a))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=report(a.root);write(a.out,result)
    print(json.dumps({k:dict(status=v['status'],profiles=len(v.get('curves',[])))
                      for k,v in result['engines'].items()}))
    print(json.dumps(result['cross_engine']))
