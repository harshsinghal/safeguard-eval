"""Verify validation selection and test metrics from published numeric evidence."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.liquid_finetune.common import *
from evals.liquid_finetune.study import select,summarize


def verify(state,validation_only=False):
    state=Path(state);v=read(state/'validation.json');f=read(state/'freeze.json')
    for rel,h in f['hashes'].items():
        if digest(state/rel)!=h:raise ValueError('Frozen evidence changed: '+rel)
    if digest(state/'registration.json')!=f['registration_sha256']:
        raise ValueError('Changed registration')
    source_root=state/'source' if (state/'source').exists() else ROOT
    for rel,h in f['sources'].items():
        if digest(source_root/rel)!=h:raise ValueError('Changed source snapshot: '+rel)
    registration=read(state/'registration.json')
    for split in ['fit','validation','test']:
        rel='metadata/'+split+'.jsonl.gz'
        if digest(state/rel)!=registration['data_hashes'][rel]:raise ValueError('Changed split')
    assert_disjoint(*(rows(state/'metadata'/(s+'.jsonl.gz')) for s in ['fit','validation','test']))
    for kind in ['frozen','finetuned']:
        chosen,grid=select(labels(v['metadata']),{k:c for k,c in v['candidates'].items() if c['kind']==kind})
        if json.loads(json.dumps(chosen))!=v['choices'][kind] or v['choices'][kind]!=f['choices'][kind]:
            raise ValueError('Selection mismatch')
        if grid!=v['grids'][kind]:raise ValueError('Validation grid mismatch')
    checked=0
    if not validation_only:
        p=read(state/'test-predictions.json');r=read(state/'results.json')
        raw=read(state/'test-output/scores.json')
        if r['freeze_sha256']!=digest(state/'freeze.json'):raise ValueError('Wrong freeze')
        if p['metadata']!=rows(state/'metadata/test.jsonl.gz'):raise ValueError('Test population differs')
        expected=summarize(p['metadata'],p['predictions'])
        if any(r[k]!=val for k,val in expected.items()):raise ValueError('Test metric/bootstrap mismatch')
        y=labels(p['metadata'])
        for kind,profiles in p['predictions'].items():
            for profile,record in profiles.items():
                selection=f['choices'][kind][profile]
                if record['candidate']!=selection['candidate'] or record['threshold']!=selection['threshold']:
                    raise ValueError('Test used another setting')
                candidate=v['candidates'][record['candidate']]
                if record['seeds']!=candidate['seeds']:raise ValueError('Seed selection or missing seed')
                if kind=='finetuned':
                    for path,s in zip(candidate['parameters'],record['scores']):
                        replay=raw['checkpoints'][path]
                        if replay['scores']!=s or replay['sha256']!=f['selected_checkpoints'][path]:
                            raise ValueError('Test output is not from frozen checkpoint')
                        if replay['validation_reload_max_abs_error']>1e-6:
                            raise ValueError('Checkpoint validation replay failed')
                for s,m in zip(record['scores'],r['profiles'][profile][kind]['seed_metrics']):
                    pred=np.asarray(s)>=record['threshold']
                    fp=int(((y==0)&pred).sum());fn=int(((y==1)&~pred).sum())
                    accuracy=1-(fp+fn)/len(y)
                    if abs(accuracy-m['accuracy'])>1e-15 or fp!=m['false_blocks'] or fn!=m['missed_violations']:
                        raise ValueError('Independent confusion check failed')
                    checked+=1
    out=dict(created_utc=now(),validation_candidates=len(v['candidates']),
             validation_profiles=8,verified_metric_rows=checked,verified_paired_profiles=0 if validation_only else 2,
             full_gpu_refit=False,checkpoint_validation_replay='Recorded in test-output/scores.json',
             validation_only=validation_only)
    write(state/('validation-verification.json' if validation_only else 'verification.json'),out)
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--validation-only',action='store_true')
    verify(**vars(p.parse_args()))
