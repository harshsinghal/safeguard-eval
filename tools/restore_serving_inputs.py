"""Restore the exact unlabeled serving workload from pinned WildGuard parquets."""
import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.ensemble.common import read,write_rows,digest
from tools.restore_liquid_inputs import SOURCE_SHA256


def restore(protocol,output,train,test):
    import pyarrow.parquet as pq
    protocol,output=Path(protocol),Path(output)
    registration=read(protocol/'registration.json')
    workload=read(protocol/'workload.json')
    for split,kind,source in [('tune','train',Path(train)),('measure','test',Path(test))]:
        if digest(source)!=SOURCE_SHA256[kind]:raise ValueError('Wrong source parquet: '+kind)
        prompts=pq.read_table(source,columns=['prompt']).column('prompt').to_pylist()
        restored=[]
        for row in workload['splits'][split]['ids']:
            prompt=prompts[int(row['id'].split('-')[1])]
            if hashlib.sha256(prompt.encode()).hexdigest()!=row['prompt_sha256']:
                raise ValueError('Prompt hash mismatch')
            restored.append(dict(id=row['id'],prompt=prompt,prompt_sha256=row['prompt_sha256']))
        destination=output/'inputs'/(split+'.jsonl')
        if destination.exists():raise ValueError('Will not overwrite existing input')
        write_rows(destination,restored)
        if digest(destination)!=registration['inputs'][split]:raise ValueError('Input file hash mismatch')
        print('Restored',split,len(restored),'exact hash verified; labels excluded')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--protocol',required=True);p.add_argument('--output',required=True)
    p.add_argument('--train',required=True);p.add_argument('--test',required=True)
    restore(**vars(p.parse_args()))
