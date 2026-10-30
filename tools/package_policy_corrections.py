"""Publish an allowlisted, prompt-free policy-correction evidence bundle."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.policy_corrections.common import read,write,digest,now
from evals.policy_corrections.study import check_freeze


def package(state,out):
    state=Path(state).resolve();out=Path(out).resolve();work=state.parent
    check_freeze(state);billing=read(work/'billing.json')
    if billing['status']!='terminated' or billing['cumulative_cost_usd']>20:raise ValueError('Confirm termination/budget first')
    out.mkdir(parents=True,exist_ok=False)
    def copy(src,rel):
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    for name in ['data-manifest.json','registration.json','prior-use-audit.json','discovery-summary.json',
        'discovery-errors.jsonl.gz','error-review.json','authoring.json','shield-selection.json',
        'freeze.json','results.json','verification.json']:
        copy(state/name,name)
    for sub in ['policies','metadata','outputs']:
        for p in sorted((state/sub).rglob('*')):
            if p.is_file():copy(p,p.relative_to(state))
    copy(work/'billing.json','billing.json')
    for name in ['setup.log','shield-development.log','qwen-validation.log','final.log',
                 'correction-freeze.txt','gpu-environment.txt']:
        copy(work/name,Path('runtime')/name)
    write(out/'runtime/cpu-environment.json',dict(python=platform.python_version(),platform=platform.platform(),
        packages={n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn']}))
    rt={}
    for p in sorted((state/'outputs').glob('*/*/*.json')):
        o=read(p);rr=o['records'];valid=[r for r in rr if r['score'] is not None]
        rt[str(p.relative_to(state/'outputs'))]=dict(n=len(rr),valid=len(valid),seconds=o['seconds'],
            median_seconds=float(np.median([r['seconds'] for r in rr])),
            p95_seconds=float(np.quantile([r['seconds'] for r in rr],.95)),
            peak_gpu_bytes=o['peak_gpu_bytes'],max_tokens=max(r['tokens'] for r in valid),
            top_token_outside_pair=sum(not r['top_token_is_label'] for r in valid),
            parity_max_difference=max([r['native_parity_difference'] for r in valid if r['native_parity_difference'] is not None],default=None))
    write(out/'runtime-summary.json',dict(measurements=rt,note='Instrumented single-example scoring, including tokenization and development parity checks. Qwen used fallback Torch linear attention. Not a production-serving benchmark.'))
    sources=read(state/'registration.json')['sources']
    for rel,h in sources.items():
        copy(ROOT/rel,Path('source')/rel)
        if digest(out/'source'/rel)!=h:raise ValueError('Registered source changed')
        for parent in Path(rel).parents:
            init=ROOT/parent/'__init__.py'
            if parent!=Path('.') and init.exists():copy(init,Path('source')/parent/'__init__.py')
    for name in ['report_policy_corrections.py','restore_policy_corrections_inputs.py','package_policy_corrections.py','plot_policy_corrections.py']:
        copy(ROOT/'tools'/name,Path('source/tools')/name)
    copy(ROOT/'tests/test_policy_corrections.py','source/tests/test_policy_corrections.py')
    for rel in ['published_runs/2026-10-30-shield-probe/policy.json',
                'published_runs/2026-10-30-shield-probe/feature-provenance/shieldstral/fit/records.json']:
        copy(ROOT/rel,Path('source')/rel)
    for name in ['setup.sh','qwen-validation.sh','final.sh']:
        copy(work/name,Path('source/runtime')/name)
    for name in ['PLAN.md','NOTES.md','RESULTS.md','RUNNING.md','POLICY-EDITS.md','progress.json']:
        copy(ROOT/'docs/policy-corrections'/name,name)
    for name in ['PLAN.md','RUNNING.md']:
        p=out/name;t=p.read_text().replace('../shield-probe/','../../docs/shield-probe/').replace('../research-directions/','../../docs/research-directions/')
        p.write_text(t)
    t=(ROOT/'docs/policy-corrections/README.md').read_text().replace('../leaderboard/','../../docs/leaderboard/').replace('../shield-probe/','../../docs/shield-probe/')
    (out/'READOUT.md').write_text(t)
    for p in (ROOT/'docs/policy-corrections/figures').glob('*'):copy(p,Path('figures')/p.name)
    r=read(state/'results.json');columns=['dataset','model','configuration','policy','threshold','n','balanced_accuracy','accuracy','macro_f1','mcc','false_blocks','missed_violations','unresolved','recall','specificity','auroc','brier','log_loss']
    with (out/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
        for split,data in r['datasets'].items():
            for model,configs in data['primary'].items():
                for name,row in configs.items():
                    rr=dict(dataset=split,model=model,configuration=name,policy=row['policy'],threshold=row['threshold'],**row['metrics'])
                    w.writerow({k:rr.get(k) for k in columns})
    write(out/'provenance.json',dict(packaged_utc=now(),protocol_commit='016d671',authoring_commit='5c347b4',
        current_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        progress=read(ROOT/'docs/policy-corrections/progress.json'),
        exclusions=['source prompts','provider/SSH credentials','private discovery-error text'],
        note='One agent-assisted revision round; original labels retained. Public test is reused; additional holdout is unused in recorded project development, not necessarily upstream checkpoint training.'))
    (out/'requirements.txt').write_text(''.join(n+'=='+importlib.metadata.version(n)+'\n' for n in ['numpy','scipy','scikit-learn']))
    (out/'README.md').write_text('''# Training-error-derived policy corrections

[Readable findings](READOUT.md) · [Registered protocol](PLAN.md) ·
[Full tables](RESULTS.md) · [CSV](results.csv) · [Reproduction](RUNNING.md)

This bundle records one bounded policy-authoring round for Shieldstral 3B and
a prespecified transfer check on Qwen3.5-4B. Model weights remain fixed. No new
classifier head or backbone fine-tuning is performed. Exact additions, source
error IDs, ambiguity flags, unused-group audit, staged freezes, all development
outputs and selected final outputs are preserved.

The additional 2,048-example project holdout comes from previously unevaluated
WildGuardTrain groups, with model-derived labels. The 1,699-example WildGuardTest
has been inspected before and remains a separate exploratory comparison. Neither
constitutes evidence of no upstream model training exposure. Source prompts are
not redistributed. All source labels are retained, including ambiguous cases.

From this directory, install the CPU requirements, then run:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m evals.policy_corrections.study verify --state .
```

This reproduces validation selection, all final operating points, category slices
and the twelve prespecified paired bootstrap contrasts without GPU calls or source
prompt text. To repeat inference, follow RUNNING.md in a fresh working directory
and restore authorized dataset inputs. Do not overwrite this immutable record.

Billing is reconciled and compute terminated; see [billing](billing.json).
The evidence remains separate from the repository's common-validation leaderboard.
Checksums cover every file except the checksum file itself. Model/data publisher
terms continue to apply.
''')
    write(out/'checksums.json',{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()})
    print('Packaged',out)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();package(a.state,a.out)
