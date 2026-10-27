"""Verify a public evidence bundle and recompute its analysis, without private data or a GPU."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile


def reproduce(bundle):
    bundle = Path(bundle).resolve()
    manifest = json.loads((bundle/'evidence-manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = bundle/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Evidence hash mismatch: '+name)
    sys.path.insert(0,str(bundle/'source'))
    spec=importlib.util.spec_from_file_location('hx_analysis',bundle/'source/docs/hatexplain/analyze.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='hatexplain-reproduction-') as tmp:
        state=Path(tmp)/'state';state.mkdir()
        for name in ('freeze.json','eligibility.json','authoring-amendment.json'):
            shutil.copyfile(bundle/name,state/name)
        shutil.copytree(bundle/'policies',state/'policies')
        for folder in sorted((bundle/'runs').iterdir()):
            dest=state/'runs'/folder.name;dest.mkdir(parents=True)
            for path in folder.iterdir():
                if path.name=='predictions.jsonl.gz':
                    decoded=gzip.decompress(path.read_bytes())
                    if hashlib.sha256(decoded).hexdigest()!=manifest['prediction_hashes'][folder.name]:
                        raise ValueError('Decompressed predictions changed')
                    (dest/'predictions.jsonl').write_bytes(decoded)
                else:
                    shutil.copyfile(path,dest/path.name)
        result=module.analyze(state,Path(tmp)/'analysis')
        recorded=json.loads((bundle/'analysis.json').read_text())
        if result!=recorded:
            raise ValueError('Analysis differs from recorded results')
    print('PASS: policies, source identities, complete predictions, selections, metrics, and paired intervals reproduce.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True)
    reproduce(**vars(p.parse_args()))
