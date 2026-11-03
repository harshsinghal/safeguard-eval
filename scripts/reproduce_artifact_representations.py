#!/usr/bin/env python3
"""Verify public hashes and reproduce results without GPU/model/API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evals.artifact_representations.report import report

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--prior',default=str(ROOT/'published_runs/2026-11-03-malicious-artifacts'))
    a=p.parse_args();run=Path(a.run).resolve();prior=Path(a.prior).resolve()
    manifest=json.loads((run/'artifact-manifest.json').read_text())
    for rel,h in manifest['files'].items():
        if hashlib.sha256((run/rel).read_bytes()).hexdigest()!=h:raise ValueError('Artifact changed: '+rel)
    expected=json.loads((run/'results.json').read_text())
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for name in ('freeze.json','metadata','predictions'):(tmp/name).symlink_to(run/name)
        report(tmp,prior,public=True)
        actual=json.loads((tmp/'results.json').read_text())
    if actual!=expected:raise ValueError('Results do not reproduce')
    print(f"Verified {len(manifest['files'])} public files; all metrics and intervals reproduce exactly.")

if __name__=='__main__':main()
