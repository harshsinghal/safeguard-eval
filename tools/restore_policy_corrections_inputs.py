"""Restore private text from authorized source files; final inputs require freeze."""
import argparse
import hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.policy_corrections.common import read,rows,write_rows,digest


def restore(state,train,test,stage):
    import pyarrow.parquet as pq
    state=Path(state);manifest=read(state/'data-manifest.json')
    if stage=='final' and not (state/'freeze.json').exists():raise ValueError('Freeze before restoring final inputs')
    paths={'train':Path(train),'test':Path(test)}
    kinds=['train','test'] if stage=='final' else ['train']
    source={}
    for kind in kinds:
        if digest(paths[kind])!=manifest['source_'+kind+'_sha256']:raise ValueError('Source hash mismatch')
        source[kind]=pq.read_table(paths[kind]).to_pylist()
    for split in (['holdout','test'] if stage=='final' else ['discovery','validation']):
        p=state/'metadata'/(split+'.jsonl.gz')
        if digest(p)!=manifest['hashes'][str(p.relative_to(state))]:raise ValueError('Assignment changed')
        output=[];kind='test' if split=='test' else 'train'
        for r in rows(p):
            original=source[kind][int(r['id'].split('-')[1])];prompt=original['prompt']
            if hashlib.sha256(prompt.encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Prompt mismatch')
            if r['expected']!={'harmful':'BLOCK','unharmful':'ALLOW'}[original['prompt_harm_label']]:raise ValueError('Label mismatch')
            output.append(dict(id=r['id'],prompt=prompt,prompt_sha256=r['prompt_sha256']))
        dest=state/'inputs'/(split+'.jsonl')
        if dest.exists():raise ValueError('Will not overwrite private inputs')
        write_rows(dest,output)
        rel=('sealed-inputs' if stage=='final' else 'inputs')+'/'+split+'.jsonl'
        if digest(dest)!=manifest['hashes'][rel]:raise ValueError('Restored input hash mismatch')
        print('Restored',split,len(output),'exact input hash matches')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--train',required=True)
    p.add_argument('--test',required=True);p.add_argument('--stage',choices=['development','final'],required=True)
    restore(**vars(p.parse_args()))
