"""Recompute the public retrieval study without datasets, GPUs or API calls."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(archive):
    archive=Path(archive).resolve();checks=json.loads((archive/'checksums.json').read_text())
    for rel,h in checks.items():
        if digest(archive/rel)!=h:raise ValueError('Changed public artifact: '+rel)
    expected=json.loads((archive/'results.json').read_text())
    with tempfile.TemporaryDirectory(prefix='retrieval-reproduce-') as tmp:
        state=Path(tmp)/'state';shutil.copytree(archive,state)
        for rel,info in json.loads((archive/'compressed-predictions.json').read_text()).items():
            dst=state/info['original_path'];dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(gzip.decompress((state/rel).read_bytes()))
            if digest(dst)!=info['uncompressed_sha256']:raise ValueError('Decompression changed bytes')
        env=dict(os.environ,PYTHONPATH=str(state/'source'))
        # Keep the recorded freeze; reconstruct a new nomination in a separate copy.
        frozen=json.loads((state/'freeze.json').read_text())
        (state/'freeze.json').unlink()
        subprocess.run([sys.executable,'-m','evals.retrieved_examples.report','freeze','--state',str(state)],
                       env=env,cwd=tmp,check=True,stdout=subprocess.DEVNULL)
        actual=json.loads((state/'freeze.json').read_text())
        for key in ['selections','validation','hashes']:
            if actual[key]!=frozen[key]:raise ValueError('Validation reproduction mismatch: '+key)
        # Restore the original freeze to check final evidence against its exact identity.
        shutil.copy2(archive/'freeze.json',state/'freeze.json')
        subprocess.run([sys.executable,'-m','evals.retrieved_examples.report','evaluate','--state',str(state)],
                       env=env,cwd=tmp,check=True,stdout=subprocess.DEVNULL)
        actual=json.loads((state/'results.json').read_text())
        for key in ['selections','test','paired']:
            if actual[key]!=expected[key]:raise ValueError('Final reproduction mismatch: '+key)
    print(json.dumps({'verified':True,'checksummed_files':len(checks),'validation_nominations':'exact',
        'test_metrics':'exact','paired_intervals':'exact','paid_inference':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);verify(**vars(p.parse_args()))
