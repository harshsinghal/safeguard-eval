"""Fetch pinned WildGuardTest only after an immutable policy freeze exists."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from evals.wildguard.data import group_prompts, write_jsonl, sha
from evals.wildguard.run import digest


def prepare(freeze,out,token_env='HF_TOKEN'):
    import pyarrow.parquet as pq
    freeze=Path(freeze);f=json.loads(freeze.read_text())
    if f.get('status')!='frozen' or not f.get('policy_editing_closed'):raise ValueError('Freeze required before test access')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    revision=f['dataset']['revision'];url=f'https://huggingface.co/datasets/allenai/wildguardmix/resolve/{revision}/test/wildguard_test.parquet'
    token=os.environ.get(token_env)
    if not token:raise ValueError('HF credential required')
    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token})
    with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
    source=out/'wildguard_test.parquet';source.write_bytes(raw)
    all_rows=pq.read_table(source).to_pylist();rows=[]
    for i,r in enumerate(all_rows):
        label=r['prompt_harm_label']
        if label is None:continue
        if label not in ('harmful','unharmful'):raise ValueError('Invalid test label')
        rows.append(dict(id=f'wgtest-{i:06}',source_index=i,prompt=r['prompt'],prompt_sha256=sha(r['prompt']),
            expected='BLOCK' if label=='harmful' else 'ALLOW',split='test',adversarial=r.get('adversarial'),
            subcategory=r.get('subcategory') or 'unspecified',agreement=r.get('prompt_harm_agreement')))
    grouping=group_prompts(rows)
    data=out/'test.jsonl';write_jsonl(data,rows)
    manifest=dict(dataset=f['dataset'],freeze_sha256=digest(freeze),source_sha256=hashlib.sha256(raw).hexdigest(),
        data_sha256=digest(data),source_rows=len(all_rows),included_rows=len(rows),excluded_null_labels=len(all_rows)-len(rows),
        grouping=grouping,includes_response=False)
    (out/'test.provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--freeze',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();prepare(a.freeze,a.out)
