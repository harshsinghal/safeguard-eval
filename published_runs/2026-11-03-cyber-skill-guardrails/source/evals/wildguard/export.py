"""Export auditable predictions while excluding gated prompts and generated reasons."""
import argparse
import gzip
import json
from pathlib import Path
import shutil

from evals.wildguard.run import digest


ALLOWED={'id','source_index','prompt_sha256','expected','split','adversarial','subcategory',
    'agreement','group','normalized_sha256','request_sha256','prediction','score','error_type',
    'latency_seconds','usage'}


def export(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True);index=[]
    for path in sorted(root.glob('*/summary.json')):
        folder=path.parent;manifest=json.loads((folder/'manifest.json').read_text())
        summary=json.loads(path.read_text())
        source=folder/'predictions.jsonl'
        rows=[json.loads(line) for line in source.read_text().split('\n') if line.strip()]
        if not summary.get('complete') or len(rows)!=len(manifest['ids']) or {r['id'] for r in rows}!=set(manifest['ids']):
            raise ValueError('Incomplete run: '+folder.name)
        target=out/'runs'/folder.name;target.mkdir(parents=True,exist_ok=False)
        for name in ('manifest.json','summary.json','policy.json'):
            if (folder/name).exists():shutil.copyfile(folder/name,target/name)
        # Explicit allowlist prevents any newly introduced textual field leaking.
        unknown=set().union(*(r.keys() for r in rows))-ALLOWED-{'reason'}
        if unknown:raise ValueError('Review unknown prediction fields: '+str(sorted(unknown)))
        clean=[{k:v for k,v in r.items() if k in ALLOWED} for r in rows]
        raw=(''.join(json.dumps(r)+'\n' for r in clean)).encode()
        dest=target/'predictions.jsonl.gz';dest.write_bytes(gzip.compress(raw,mtime=0))
        index.append(dict(run=folder.name,adapter=manifest['adapter'],policy_id=manifest['policy_id'],
            stage=manifest['stage'],n=summary['n'],accuracy=summary['accuracy'],errors=summary['errors'],
            source_predictions_sha256=digest(source),public_predictions_gzip_sha256=digest(dest),
            public_fields_removed=['reason'] if any('reason' in r for r in rows) else [],
            public_predictions='runs/'+folder.name+'/predictions.jsonl.gz'))
    (out/'run-index.json').write_text(json.dumps(index,indent=2)+'\n')
    return index


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();index=export(a.runs,a.out);print(json.dumps(dict(runs=len(index),predictions=sum(r['n'] for r in index))))
