"""Recompute published selections, metrics and intervals without gated prompt text.

Run from the repository root:
    python3 docs/policy-transfer/reproduce.py --bundle docs/policy-transfer/evidence
"""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evals.policy_transfer.analyze import analyze
from evals.policy_transfer.common import BASE, REGISTRY, digest, read, text_hash
from evals.policy_transfer.study import rank
from evals.wildguard.metrics import report


def reproduce(bundle):
    bundle=Path(bundle)
    with tempfile.TemporaryDirectory() as temporary:
        state=Path(temporary)
        for name in ('candidates.json','source-selection.json','freeze.json'):
            shutil.copy2(bundle/name,state/name)
        shutil.copytree(bundle/'policies',state/'policies')
        if digest(bundle/'registry.json')!=digest(REGISTRY):
            raise ValueError('Registry does not match published evidence')
        results={}; count=0
        for part,targetname in [('new-runs','runs'),('baseline','baseline')]:
            for entry in read(bundle/part/'run-index.json'):
                source=bundle/part/'runs'/entry['run'];target=state/targetname/entry['run']
                target.mkdir(parents=True)
                for name in ('manifest.json','summary.json','policy.json'):
                    shutil.copy2(source/name,target/name)
                zipped=source/'predictions.jsonl.gz'
                if digest(zipped)!=entry['public_predictions_gzip_sha256']:
                    raise ValueError('Published gzip hash mismatch')
                (target/'predictions.jsonl').write_bytes(gzip.decompress(zipped.read_bytes()))
                if digest(target/'predictions.jsonl')!=entry['source_predictions_sha256']:
                    raise ValueError('Predictions changed during export')
                rows=[json.loads(x) for x in (target/'predictions.jsonl').read_text().split('\n') if x]
                summary=read(target/'summary.json');manifest=read(target/'manifest.json')
                if (not summary['complete'] or [r['id'] for r in rows]!=manifest['ids']
                        or len(set(manifest['ids']))!=len(rows)):
                    raise ValueError('Incomplete population')
                if any(summary[k]!=v for k,v in report(rows).items()):
                    raise ValueError('Summary mismatch')
                if digest(target/'policy.json')!=manifest['policy_sha256']:
                    raise ValueError('Policy bytes changed')
                results[entry['run']]=(summary,rows,manifest);count+=len(rows)
        selection=read(state/'source-selection.json');f=read(state/'freeze.json')
        for slug,entries in selection['searches'].items():
            for e in entries:
                if results[e['run']][0]['accuracy']!=e['accuracy']:
                    raise ValueError('Selection score mismatch')
                if results[e['fit_run']][0]['accuracy']!=e['fit_accuracy']:
                    raise ValueError('Fitting score mismatch')
            if min(entries,key=rank)['sha256']!=selection['selected'][slug]['sha256']:
                raise ValueError('Source winner mismatch')
        for slug,entries in f['validation'].items():
            for e in entries:
                if results[e['run']][0]['accuracy']!=e['accuracy']:
                    raise ValueError('Transfer validation mismatch')
            if min(entries,key=rank)['sha256']!=f['recipient_choice'][slug]['sha256']:
                raise ValueError('Frozen recipient winner mismatch')
        actual=analyze(state,state/'recomputed.json');expected=read(bundle/'analysis.json')
        for k in expected:
            if k!='created_utc' and actual[k]!=expected[k]:
                raise ValueError('Analysis mismatch: '+k)
        return dict(verified=True,runs=len(results),predictions=count,
                    metrics='all summaries, frozen choices, matrices and paired intervals')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True)
    print(json.dumps(reproduce(parser.parse_args().bundle),indent=2))
