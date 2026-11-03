#!/usr/bin/env python3
"""Restore registered inputs as inert data, with pinned revisions and hash checks."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.malicious_artifacts.common import read,digest
from evals.malicious_artifacts.data import fetch,prepare

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run=Path(a.run).resolve();dest=Path(a.output).resolve()
    if dest.exists():raise ValueError('Choose a new output directory')
    dest.mkdir(parents=True)
    fetch(dest);prepare(dest)
    reg=read(run/'registration.json');checked=0
    for rel,h in reg['files'].items():
        if rel.startswith(('data/','metadata/')):
            if digest(dest/rel)!=h:raise ValueError('Restored input differs: '+rel)
            checked+=1
    print(f'Restored and verified {checked} data/metadata files. No artifacts executed; no model or API inference.')

if __name__=='__main__':main()
