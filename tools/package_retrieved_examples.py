"""Publish prompt-free evidence; source text, embeddings and credentials stay private."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def package(state,output):
    state,output=Path(state),Path(output)
    if output.exists():raise ValueError('Use a new immutable archive directory')
    if not (state/'results.json').exists() or not (state/'cleanup.json').exists():raise ValueError('Results and cleanup required')
    if json.loads((state/'cleanup.json').read_text())['our_instance_active']:raise ValueError('Compute still running')
    output.mkdir(parents=True)
    def copy(rel):
        src=state/rel;dst=output/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    for rel in ['registration.json','registration-v1.json','registration-v2.json','freeze.json','results.json','RESULTS.md',
                'preflight.json','billing.json','cleanup.json','jev-costs.json','bank-metadata.jsonl.gz']:
        copy(rel)
    for name in ['policies','metadata','retrieval','runtime','amendments']:
        shutil.copytree(state/name,output/name)
    compressed={}
    for src in sorted((state/'predictions').rglob('*')):
        if not src.is_file():continue
        rel=src.relative_to(state);dst=output/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        if src.suffix=='.jsonl':
            dst=dst.with_suffix('.jsonl.gz');dst.write_bytes(gzip.compress(src.read_bytes(),mtime=0))
            compressed[str(dst.relative_to(output))]={'original_path':str(rel),'uncompressed_sha256':digest(src)}
        else:shutil.copy2(src,dst)
    reg=json.loads((state/'registration.json').read_text())
    for rel,expected in reg['sources'].items():
        if digest(ROOT/rel)!=expected:raise ValueError('Registered source changed: '+rel)
        dst=output/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dst)
        parent=dst.parent
        while parent!=output/'source' and parent.is_relative_to(output/'source'):
            source_init=ROOT/parent.relative_to(output/'source')/'__init__.py'
            if source_init.exists():shutil.copy2(source_init,parent/'__init__.py')
            parent=parent.parent
    for rel in ['tools/verify_retrieved_examples.py','tools/package_retrieved_examples.py','tests/test_retrieved_examples.py']:
        dst=output/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dst)
    for n in ['PLAN.md','NOTES.md','RUNNING.md']:shutil.copy2(ROOT/'docs/retrieved-examples'/n,output/n)
    (output/'compressed-predictions.json').write_text(json.dumps(compressed,indent=2)+'\n')
    (output/'README.md').write_text('# Retrieved-example accuracy study\n\n'
        'Frozen policy-only, fixed-four, nearest-four and balanced-nearest comparisons for '
        'PolicyLM, Shieldstral, Kev and Jev, plus a shared nearest-neighbor vote. No calibration.\n\n'
        'See [results](RESULTS.md), [protocol](PLAN.md), [research notes](NOTES.md), '
        '[costs](billing.json), and [cleanup](cleanup.json). Source prompts and embeddings are excluded.\n\n'
        'Reproduce on CPU from a checkout of the repository:\n\n```bash\n'
        'python3 tools/verify_retrieved_examples.py --archive '+str(output.relative_to(ROOT))+'\n```\n\n'
        'The verifier checks all hashes, restores compressed predictions in a temporary folder, '
        'and recomputes validation nominations, final metrics and paired bootstrap differences.\n')
    checks={str(p.relative_to(output)):digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({'files':len(checks),'bytes':sum(p.stat().st_size for p in output.rglob('*') if p.is_file())}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--output',required=True)
    package(**vars(p.parse_args()))
