#!/usr/bin/env python3
"""Verify and recompute the published artifact leaderboards without inference."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.malicious_artifacts.common import read,digest
from evals.malicious_artifacts.report import report

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args();run=Path(args.run).resolve()
    manifest=read(run/'artifact-manifest.json')
    for rel,h in manifest['files'].items():
        if digest(run/rel)!=h:raise ValueError('Published artifact differs: '+rel)
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)
        for rel in ['metadata','predictions']:shutil.copytree(run/rel,target/rel)
        shutil.copy2(run/'freeze.json',target/'freeze.json')
        with contextlib.redirect_stdout(io.StringIO()):report(target,verify_sources=False)
        actual=read(target/'results.json');expected=read(run/'results.json')
        if actual['tasks']!=expected['tasks']:raise ValueError('Recomputed metrics differ from release')
    print(json.dumps({'verified_files':len(manifest['files']),'recomputed_tasks':list(actual['tasks']),
        'paid_inference':False,'dataset_downloads':False,'matches':True}))

if __name__=='__main__':main()
