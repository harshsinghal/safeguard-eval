"""Publish numeric evidence and source; exclude prompts, features and large weights."""
import argparse
import importlib.metadata
import platform
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.liquid_finetune.common import *


def package(state,out):
    state,out=Path(state).resolve(),Path(out).resolve();f=check_freeze(state)
    bill=read(state/'billing.json')
    if bill['status']!='terminated' or bill['cumulative_accounted_usd']>20:
        raise ValueError('Compute resources not closed or budget exceeded')
    out.mkdir(parents=True,exist_ok=False)
    def copy(src,rel):
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    for name in ['registration.json','PLAN.md','AMENDMENTS.md','RUN-LOG.md','references.json',
                 'smoke.json','validation.json','freeze.json','test-predictions.json','results.json',
                 'verification.json','validation-verification.json','billing.json','gpu-billing.json',
                 'checkpoint-inventory.json','progress.json']:
        copy(state/name,name)
    for p in (state/'metadata').glob('*.gz'):copy(p,p.relative_to(state))
    for p in (state/'fits').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.npz']:copy(p,p.relative_to(state))
    for p in (state/'features').rglob('manifest.json'):copy(p,p.relative_to(state))
    copy(state/'test-output/scores.json','test-output/scores.json')
    for rel,h in f['sources'].items():
        copy(ROOT/rel,Path('source')/rel)
        if digest(out/'source'/rel)!=h:raise ValueError('Source hash mismatch')
    for sub in ['evals','evals/ensemble','evals/leaderboard']:
        copy(ROOT/sub/'__init__.py',Path('source')/sub/'__init__.py')
    for name in ['verify_liquid_finetune.py','restore_liquid_inputs.py','report_liquid_finetune.py','package_liquid_finetune.py']:
        copy(ROOT/'tools'/name,Path('source/tools')/name)
    copy(ROOT/'tests/test_liquid_finetune.py','source/tests/test_liquid_finetune.py')
    for p in (state/'runtime').iterdir():
        if p.is_file():copy(p,Path('runtime')/p.name)
    for name in ['README.md','RESULTS.md','results.csv','RUNNING.md','AMENDMENTS.md']:
        copy(ROOT/'docs/liquid-finetune'/name,'READOUT.md' if name=='README.md' else name)
    for name in ['READOUT.md','RUNNING.md']:
        p=out/name;s=p.read_text()
        s=s.replace('../../published_runs/2026-10-31-liquid-finetune/README.md','README.md')
        s=s.replace('../COMPUTE.md','../../docs/COMPUTE.md')
        for folder in ['contrastive-heads','activation-probe','leaderboard']:
            s=s.replace('../'+folder+'/', '../../docs/'+folder+'/')
        p.write_text(s)
    cpu=dict(python=platform.python_version(),packages={n:importlib.metadata.version(n) for n in
        ['numpy','scipy','scikit-learn','torch','threadpoolctl']})
    write(out/'runtime/cpu-environment.json',cpu)
    (out/'requirements-cpu.txt').write_text(''.join(k+'=='+v+'\n' for k,v in cpu['packages'].items()))
    progress=read(state/'progress.json')
    public_progress={k:v for k,v in progress.items() if k!='published'}
    public_progress['publication_note']='Prepared before Git publication; the containing repository commit is the publication record.'
    write(out/'progress.json',public_progress)
    write(out/'provenance.json',dict(packaged_utc=now(),protocol_commit='164afe0',
        pre_test_freeze_commit=progress['pre_test_freeze_commit'],
        model=MODEL,revision=REVISION,retained_weights=read(state/'checkpoint-inventory.json'),
        private_exclusions=['submitted prompts','pooled embeddings','large encoder weights','credentials'],
        public_verification='Validation selections, test metrics, paired intervals and assignments; no GPU refit.',
        checkpoint_replay='Every selected GPU checkpoint replayed its validation scores before test inference.'))
    (out/'README.md').write_text('''# Fine-tuning a Liquid encoder on WildGuard

[Readable findings](READOUT.md) · [Full results](RESULTS.md) · [CSV](results.csv) ·
[Registered plan](PLAN.md) · [Execution notes](AMENDMENTS.md) · [Reproduction](RUNNING.md)

This study compares a trained linear classifier on frozen Liquid encoder features
with end-to-end supervised fine-tuning of that same encoder and a linear head.
The input is a submitted prompt. No policy text is supplied. Fitting uses 4,096
WildGuardTrain prompts, validation 1,536, and test all 1,699 labeled prompts in
the official WildGuardTest population. That public test has been used previously.

The bundle includes every validation candidate, all four operating profiles,
all selected fine-tuning seeds, predictions, metrics, paired intervals, split
identities, source snapshots, parameter hashes, runtime and billing evidence.
The small frozen classifier weights are included. Text, embeddings, credentials
and large fine-tuned checkpoints are not. See checkpoint-inventory.json for
the local weight retention record.

Verify a copy without GPUs or API calls:

```sh
PYTHONPATH=source python3 source/tools/verify_liquid_finetune.py --state .
```

Verification writes a new verification.json; use a copy to preserve the original
checksums. Every package file except checksums.json itself is listed there.
''')
    write(out/'checksums.json',{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()})
    print('Packaged',out,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    package(**vars(p.parse_args()))
