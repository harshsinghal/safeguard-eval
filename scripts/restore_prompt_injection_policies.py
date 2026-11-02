"""Restore exact example-bearing policies from pinned, privately downloaded inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.prompt_injection.common import MODELS,rows,write,read,digest
from evals.prompt_injection.policies import initial,with_examples,render


def restore(archive,data_state,out):
    archive=Path(archive);data_state=Path(data_state);out=Path(out)
    reg=read(archive/'registration.json');fit_path=data_state/'data/fit.jsonl'
    if digest(fit_path)!=reg['files']['data/fit.jsonl']:raise ValueError('Fitting inputs differ from the registered population')
    fit={r['id']:r for r in rows(fit_path)};frozen=read(archive/'policy-freeze.json')
    for slug in MODELS:
        prov=read(archive/f'policies/{slug}/example-provenance.json');examples=[]
        for r in prov:
            original=fit[r['id']]
            if any(original[k]!=r[k] for k in ('expected','prompt_sha256','group')):raise ValueError('Example provenance mismatch')
            examples.append(original)
        pp=initial();pp['examples']=with_examples(examples);value={pid:render(p,slug) for pid,p in pp.items()}
        path=out/slug/'candidates.json'
        if path.exists():raise ValueError('Do not overwrite an existing policy file')
        write(path,value)
        if digest(path)!=frozen['files'][f'policies/{slug}/candidates.json']:raise ValueError('Restored policy does not match the frozen hash')
    print('Restored and hash-verified policies for all six models. Keep quoted dataset text private.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--data-state',required=True);p.add_argument('--out',required=True)
    restore(**vars(p.parse_args()))
