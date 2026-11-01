"""Audit the frozen L4 serving evidence without GPU/API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.report_cloud_serving import report
from evals.serving.cloud_lengths import rows, sha
from evals.serving.cloud_shield_smoke import normalized_score


def verify(root):
    sums = json.loads((root/'SHA256SUMS.json').read_text())
    for name, digest in sums.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest, name
    reg = json.loads((root/'registration.json').read_text())
    freeze = json.loads((root/'input-freeze.json').read_text())
    manifest = json.loads((root/'input-manifest.json').read_text())
    assert freeze['registration_sha256']==sha(reg)
    assert freeze['manifest_sha256']==sha(manifest)
    assert freeze['policy_sha256']==sha(json.loads((root/'policy.json').read_text()))
    amendment=json.loads((root/'runtime-amendment.json').read_text())
    assert hashlib.sha256((root/'source/cloud_lengths-initial.py').read_bytes()).hexdigest()==reg['code_sha256']
    assert hashlib.sha256((root/'source/cloud_lengths.py').read_bytes()).hexdigest()==amendment['revised_source_sha256']
    for name, group in manifest.items():
        assert len(group)==64 and len({r['input_sha256'] for r in group})==64
        if name not in ('fit','mixed'):
            assert all(r['content_tokens']==int(name) for r in group)
        assert all(r['full_tokens']+8<=8192 for r in group)
    result = report(root)
    assert result == json.loads((root/'results.json').read_text())
    passes=0;count=0
    for engine in ('vllm','sglang'):
        d=root/engine
        traces=list(d.glob('measure-*.jsonl'))+list((root/'long-input-control'/engine).glob('measure-*.jsonl'))
        for p in traces:
            group=p.stem.split('-')[1]
            expected={r['id']:r['input_sha256'] for r in manifest[group]}
            records=rows(p)
            assert {r['id']:r['input_sha256'] for r in records}==expected
            passes+=1;count+=len(records)
        if (d/'freeze.json').exists():
            f=json.loads((d/'freeze.json').read_text())
            for candidate in f['candidates']:
                assert candidate['errors']==0 and candidate['decision_changes']<=1
                n=candidate['parameter']
                a={r['id']:r for r in rows(d/f'parity-p{n}.jsonl')}
                b={r['id']:r for r in rows(d/f'tune-p{n}.jsonl')}
                assert len(a)==32 and len(b)==64 and a.keys()<=b.keys()
                assert candidate['decision_changes']==sum(a[i]['prediction']!=b[i]['prediction'] for i in a)
    bill=json.loads((root/'billing.json').read_text())
    assert bill['status']=='terminated' and bill['cost_usd']<=1.22
    assert bill['cumulative_accounted_usd']<=20
    for shield in [root/'shieldstral-canary',root/'shieldstral-initial']:
        if not shield.exists(): continue
        for engine in ('vllm','sglang'):
            d=shield/engine
            if not (d/'result.json').exists(): continue
            serial,batch=rows(d/'serial.jsonl'),rows(d/'batch.jsonl')
            saved=json.loads((d/'result.json').read_text())
            assert len(serial)==len(batch)==32
            for r in serial+batch:
                if r['prediction']=='ERROR': continue
                assert r['full_tokens']==r['prompt_tokens']
                assert normalized_score(r['label_logprobs'])==r['score']
                assert r['prediction']==('BLOCK' if r['score']>=.5 else 'ALLOW')
            assert saved['errors']==sum(r['prediction']=='ERROR' for r in serial+batch)
            assert saved['label_changes']==sum(a['prediction']!=b['prediction'] for a,b in zip(serial,batch))
            differences=[abs(a['score']-b['score']) for a,b in zip(serial,batch) if 'score' in a and 'score' in b]
            assert saved['max_score_difference']==max(differences,default=None)
            assert saved['accepted']==(saved['errors']==0 and saved['label_changes']<=1
                                        and saved['max_score_difference']<=.02)
    print(json.dumps(dict(verified_passes=passes,requests=count,cost_usd=bill['cost_usd'],
                          cross_engine=result['cross_engine'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    verify(p.parse_args().root)
