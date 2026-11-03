#!/usr/bin/env python3
"""Verify public files and reproduce metrics without models or paid calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evals.cyber_skill_guardrails.report import report

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run).resolve()
    manifest=json.loads((run/'artifact-manifest.json').read_text())
    for rel,h in manifest['files'].items():
        path=(run/rel).resolve()
        if not path.is_relative_to(run):raise ValueError('Unsafe manifest path')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=h:raise ValueError('Artifact changed: '+rel)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for name in ('freeze.json','metadata','predictions'):(tmp/name).symlink_to(run/name)
        report(tmp,public=True)
        if json.loads((tmp/'results.json').read_text())!=json.loads((run/'results.json').read_text()):raise ValueError('Results differ')
    print(f"Verified {len(manifest['files'])} files; metrics and intervals reproduce exactly.")

if __name__=='__main__':main()
