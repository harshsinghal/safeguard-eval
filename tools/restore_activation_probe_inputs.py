"""Restore exact private encoder inputs from authorized pinned WildGuard Parquet files."""
import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.activation_probe.common import read, rows, write_rows, digest

SOURCE_SHA256 = {
    'train':'02ecea8a724a9146a1e473a95a7cdf262adfe9c7d5408953ca86d2fcfbdc8953',
    'test':'6ccc2909c1ae6d41424fac69f1fc32535b1de39cb8f80407d81e8bc64a0bebca',
}


def restore(state, source, stage):
    import pyarrow.parquet as pq
    state,source=Path(state),Path(source)
    kind='test' if stage=='test' else 'train'
    if digest(source)!=SOURCE_SHA256[kind]:raise ValueError('Wrong pinned publisher source file')
    if stage=='test' and not (state/'freeze.json').exists():
        raise ValueError('Restore test inputs only after development selection is frozen')
    original=pq.read_table(source).to_pylist();manifest=read(state/'data-manifest.json')
    for split in (['test'] if stage=='test' else ['fit','validation']):
        metadata=state/'metadata'/(split+'.jsonl.gz')
        if digest(metadata)!=manifest['hashes'][str(metadata.relative_to(state))]:
            raise ValueError('Published assignments changed')
        output=[]
        for r in rows(metadata):
            expected_prefix='wgtest-' if split=='test' else 'wgtrain-'
            if not r['id'].startswith(expected_prefix):raise ValueError('Wrong source population')
            record=original[int(r['id'].split('-')[1])];prompt=record['prompt']
            if hashlib.sha256(prompt.encode()).hexdigest()!=r['prompt_sha256']:
                raise ValueError('Prompt identity changed')
            expected={'harmful':'BLOCK','unharmful':'ALLOW'}[record['prompt_harm_label']]
            if expected!=r['expected']:raise ValueError('Ground truth changed')
            output.append(dict(id=r['id'],prompt=prompt,prompt_sha256=r['prompt_sha256']))
        out=state/'inputs'/(split+'.jsonl')
        if out.exists():raise ValueError('Do not overwrite existing private inputs')
        write_rows(out,output)
        if digest(out)!=manifest['hashes'][str(out.relative_to(state))]:
            raise ValueError('Restored encoder inputs do not match recorded hash')
        print('Restored',split,len(output),'rows; exact input hash verified')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',required=True);p.add_argument('--source',required=True)
    p.add_argument('--stage',choices=['development','test'],required=True)
    restore(**vars(p.parse_args()))
