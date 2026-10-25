"""Verify published hashes and recompute scores without a GPU or gated text."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from evals.wildguard.metrics import report
from evals.wildguard.run import digest


def reproduce(evidence,out,intervals=False):
    evidence=Path(evidence);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    index=json.loads((evidence/'run-index.json').read_text());verified=[]
    for item in index:
        source=evidence/item['public_predictions']
        if digest(source)!=item['public_predictions_gzip_sha256']:raise ValueError('Prediction archive changed')
        raw=gzip.decompress(source.read_bytes())
        if not item['public_fields_removed'] and hashlib.sha256(raw).hexdigest()!=item['source_predictions_sha256']:
            raise ValueError('Unredacted source predictions differ')
        rows=[json.loads(line) for line in raw.decode().split('\n') if line.strip()]
        folder=out/item['run'];folder.mkdir()
        (folder/'predictions.jsonl').write_bytes(raw)
        for name in ('manifest.json','summary.json','policy.json'):
            path=source.parent/name
            if path.exists():shutil.copyfile(path,folder/name)
        manifest=json.loads((folder/'manifest.json').read_text());expected=json.loads((folder/'summary.json').read_text())
        if len(rows)!=len(manifest['ids']) or {r['id'] for r in rows}!=set(manifest['ids']):raise ValueError('Incomplete population')
        actual=report(rows)
        for key,value in actual.items():
            if value!=expected[key]:raise ValueError('Metric mismatch: '+item['run']+'/'+key)
        verified.append(dict(run=item['run'],n=len(rows),accuracy=actual['accuracy']))
    if intervals:
        from evals.wildguard.analyze import analyze
        analysis=analyze(out,evidence/'freeze.json',evidence/'train-test-overlap.json')
        (out/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
        if analysis!=json.loads((evidence/'analysis.json').read_text()):raise ValueError('Paired analysis differs')
    result=dict(verified_runs=len(verified),predictions=sum(r['n'] for r in verified),metrics_match=True,
        intervals_reproduced=intervals,runs=verified)
    (out/'reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);p.add_argument('--intervals',action='store_true')
    a=p.parse_args();r=reproduce(a.evidence,a.out,a.intervals);print(json.dumps({k:v for k,v in r.items() if k!='runs'}))
