"""Reproduce the published injection tables from hashed, prompt-free predictions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evals.prompt_injection.common import MODELS,measures
from evals.prompt_injection.report import intervals


def read(path):return json.loads(Path(path).read_text())
def rows(path):
    with gzip.open(path,'rt') as f:return [json.loads(line) for line in f if line.strip()]


def reproduce(archive,out):
    archive=Path(archive);out=Path(out)
    hashes=read(archive/'checksums.json')
    for rel,h in hashes.items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('Unsafe archive path')
        if hashlib.sha256((archive/rel).read_bytes()).hexdigest()!=h:raise ValueError('Artifact changed: '+rel)
    frozen=read(archive/'freeze.json');metadata=rows(archive/'metadata/test.jsonl.gz');by_id={r['id']:r for r in metadata}
    if len(by_id)!=len(metadata):raise ValueError('Duplicate test IDs')
    systems={}
    for slug in MODELS:
        for arm,pid in [('brief','brief'),('selected',frozen['selected'][slug])]:
            rr=rows(archive/f'predictions/{slug}/test/{pid}.jsonl.gz')
            if len(rr)!=len(metadata) or {r['id'] for r in rr}!=set(by_id):raise ValueError('Incomplete population')
            for r in rr:
                if r['policy_id']!=pid or r['prediction'] not in ('ALLOW','BLOCK','ERROR'):raise ValueError('Policy identity or decision mismatch')
                if any(r[k]!=by_id[r['id']][k] for k in ('expected','group','split','prompt_sha256','dataset')):raise ValueError('Metadata mismatch')
            systems[slug+'/'+arm]=rr
    result={}
    for ds in sorted({r['dataset'] for r in metadata}):
        ss={k:[r for r in rr if r['dataset']==ds] for k,rr in systems.items()}
        mm=[r for r in metadata if r['dataset']==ds]
        result[ds]={'metrics':{k:measures(v) for k,v in ss.items()},'uncertainty':intervals(mm,ss)}
    expected=read(archive/'summary.json')['datasets']
    if result!=expected:raise ValueError('Reproduced metrics or intervals differ from the published report')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'verified_artifacts':len(hashes),'test_examples':len(metadata),'systems':len(systems),'datasets':list(result),'matches_published_summary':True}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    reproduce(**vars(p.parse_args()))
