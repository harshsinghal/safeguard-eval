"""Audit the frozen L4 serving evidence without GPU/API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.report_cloud_serving import report
from evals.serving.cloud_lengths import rows, sha, summary
from evals.serving.cloud_shield_smoke import normalized_score


def verify(root):
    sums = json.loads((root/'SHA256SUMS.json').read_text())
    actual={str(p.relative_to(root)) for p in root.rglob('*')
            if p.is_file() and p.name!='SHA256SUMS.json'}
    assert set(sums)==actual, 'Manifest must cover every published file'
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
    control=json.loads((root/'long-control-registration.json').read_text())
    assert hashlib.sha256((root/'source/cloud_long_control.py').read_bytes()).hexdigest()==control['code_sha256']
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
        assert (d/'complete.json').exists()
        assert (root/'long-input-control'/engine/'complete.json').exists()
        traces=list(d.glob('measure-*.jsonl'))+list((root/'long-input-control'/engine).glob('measure-*.jsonl'))
        assert len(traces)==34
        for p in traces:
            group=p.stem.split('-')[1]
            expected={r['id']:r['input_sha256'] for r in manifest[group]}
            records=rows(p)
            assert len(records)==len(expected)
            assert {r['id']:r['input_sha256'] for r in records}==expected
            for r in records:
                assert r['prediction'] in ('ALLOW','BLOCK')
                assert r['finish_reason']=='stop' and r['text'].strip() in ('A','B')
                assert r['prediction']==('ALLOW' if r['text'].strip()=='A' else 'BLOCK')
                assert r['usage']['prompt_tokens']==r['full_tokens']
            passes+=1;count+=len(records)
        if (d/'freeze.json').exists():
            f=json.loads((d/'freeze.json').read_text())
            for candidate in f['candidates']:
                assert candidate['errors']==0 and candidate['decision_changes']<=1
                n=candidate['parameter']
                a={r['id']:r for r in rows(d/f'parity-p{n}.jsonl')}
                b={r['id']:r for r in rows(d/f'tune-p{n}.jsonl')}
                assert len(a)==32 and len(b)==64 and a.keys()<=b.keys()
                expected_fit={r['id']:r['input_sha256'] for r in manifest['fit']}
                assert {i:r['input_sha256'] for i,r in b.items()}==expected_fit
                assert all(r['input_sha256']==expected_fit[i] for i,r in a.items())
                assert candidate['decision_changes']==sum(a[i]['prediction']!=b[i]['prediction'] for i in a)
                recomputed=summary(list(b.values()),candidate['wall_seconds'])
                for key,value in recomputed.items(): assert candidate[key]==value,(engine,n,key)
    assert (passes,count)==(68,4352)
    bill=json.loads((root/'billing.json').read_text())
    assert bill['status']=='terminated' and bill['cost_usd']<=1.22
    assert bill['cumulative_accounted_usd']<=20
    assert bill['cumulative_accounted_usd']==bill['prior_cumulative_accounted_usd']+bill['cost_usd']
    assert bill['cost_usd']==sum(r['cost_cents'] for r in bill['usage'])/100
    assert bill['gpu_seconds']==sum(r['gpu_seconds'] for r in bill['usage'])
    cleanup=json.loads((root/'cleanup.json').read_text())
    assert not cleanup['our_instance_active'] and cleanup['provider_active_instance_count']==0
    assert cleanup['temporary_provider_key_removed'] and cleanup['temporary_local_key_removed']
    for shield in [root/'shieldstral-canary',root/'shieldstral-initial',root/'shieldstral-hf-canary']:
        if not shield.exists(): continue
        expected={r['id']:r['input_sha256'] for r in json.loads((shield/'input-manifest.json').read_text())}
        assert len(expected)==32
        for engine in ('vllm','sglang'):
            d=shield/engine
            if not (d/'result.json').exists(): continue
            serial,batch=rows(d/'serial.jsonl'),rows(d/'batch.jsonl')
            saved=json.loads((d/'result.json').read_text())
            assert len(serial)==len(batch)==32
            assert [r['id'] for r in serial]==[r['id'] for r in batch]
            for records in (serial,batch):
                assert {r['id']:r['input_sha256'] for r in records}==expected
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
    hf=json.loads((root/'shieldstral-hf-canary/registration.json').read_text())
    assert hashlib.sha256((root/'source/cloud_shield_smoke.py').read_bytes()).hexdigest()==hf['code_sha256']
    assert hashlib.sha256((root/'source/prepare-shield-hf.py').read_bytes()).hexdigest()==hf['preparation_source_sha256']
    initial=json.loads((root/'shieldstral-initial/registration.json').read_text())
    assert hashlib.sha256((root/'source/cloud_shield_smoke-initial.py').read_bytes()).hexdigest()==initial['code_sha256']
    print(json.dumps(dict(verified_passes=passes,requests=count,cost_usd=bill['cost_usd'],
                          cross_engine=result['cross_engine'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    verify(p.parse_args().root)
