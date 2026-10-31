"""Restore private WildGuard inputs with strict source and assignment hashes."""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.ensemble.common import read,rows,write,write_rows,digest,now

SOURCE_SHA256={
    'train':'02ecea8a724a9146a1e473a95a7cdf262adfe9c7d5408953ca86d2fcfbdc8953',
    'test':'6ccc2909c1ae6d41424fac69f1fc32535b1de39cb8f80407d81e8bc64a0bebca',
}


def initialize(state,protocol):
    state,protocol=Path(state),Path(protocol)
    registration=read(protocol/'registration.json')
    for split in ['fit','validation','test']:
        rel='metadata/'+split+'.jsonl.gz'
        if digest(protocol/rel)!=registration['data_hashes'][rel]:raise ValueError('Changed published assignments')
    state.mkdir(parents=True,exist_ok=False)
    for name in ['registration.json','PLAN.md']:
        shutil.copy2(protocol/name,state/name)
    shutil.copytree(protocol/'metadata',state/'metadata')
    write(state/'replication.json',dict(created_utc=now(),original_registration_sha256=digest(protocol/'registration.json'),
        note='Fresh execution of an existing protocol. No original weights, freeze or results copied.'))
    print('Initialized new execution directory from published protocol')


def restore(state,source,stage):
    import pyarrow.parquet as pq
    state,source=Path(state),Path(source);kind='test' if stage=='test' else 'train'
    if digest(source)!=SOURCE_SHA256[kind]:raise ValueError('Wrong source parquet')
    if stage=='test' and not (state/'freeze.json').exists():raise ValueError('Freeze before restoring test')
    original=pq.read_table(source).to_pylist();registration=read(state/'registration.json')
    for split in (['test'] if stage=='test' else ['fit','validation']):
        rel='metadata/'+split+'.jsonl.gz'
        if digest(state/rel)!=registration['data_hashes'][rel]:raise ValueError('Changed assignments')
        output=[]
        for r in rows(state/rel):
            prefix='wgtest-' if split=='test' else 'wgtrain-'
            if not r['id'].startswith(prefix):raise ValueError('Wrong population')
            row=original[int(r['id'].split('-')[1])];prompt=row['prompt']
            if hashlib.sha256(prompt.encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Wrong prompt')
            if {'harmful':'BLOCK','unharmful':'ALLOW'}[row['prompt_harm_label']]!=r['expected']:
                raise ValueError('Wrong label')
            output.append(dict(id=r['id'],prompt=prompt,prompt_sha256=r['prompt_sha256']))
        rel='inputs/'+split+'.jsonl'
        if (state/rel).exists():raise ValueError('Will not overwrite existing input')
        write_rows(state/rel,output)
        if digest(state/rel)!=registration['data_hashes'][rel]:raise ValueError('Restored file hash mismatch')
        print('Restored',split,len(output),'exact hash verified')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--source')
    p.add_argument('--stage',choices=['development','test']);p.add_argument('--protocol')
    a=p.parse_args()
    if a.protocol:
        if a.source or a.stage:p.error('Initialize separately from restoration')
        initialize(a.state,a.protocol)
    else:
        if not a.source or not a.stage:p.error('Restoration needs --source and --stage')
        restore(a.state,a.source,a.stage)
