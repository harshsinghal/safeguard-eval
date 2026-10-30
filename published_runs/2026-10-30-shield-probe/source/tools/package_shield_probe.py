"""Publish prompt-free evidence; never copy encoder inputs or feature vectors."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evals.shield_probe.common import read, write, digest, now
from evals.shield_probe.study import check_freeze


def package(state,out):
    state,out=Path(state).resolve(),Path(out).resolve();work=state.parent
    freeze=check_freeze(state,include_features=True)
    billing=read(work/'billing.json')
    if billing['status']!='terminated' or billing['cumulative_cost_usd']>20:
        raise ValueError('Verify termination and cumulative budget before publication')
    out.mkdir(parents=True,exist_ok=False)
    def copy(src,relative):
        dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    for name in ['data-manifest.json','registration.json','policy.json','freeze.json','validation.json',
                 'fits.json','test-predictions.json','test-results.json','verification.json',
                 'refit-reproduction.json','runtime-summary.json']:
        copy(state/name,name)
    for sub in ['metadata','fits']:
        for p in sorted((state/sub).glob('*')):copy(p,Path(sub)/p.name)
    for p in sorted((state/'features').glob('*/*/*.json')):
        copy(p,Path('feature-provenance')/p.relative_to(state/'features'))
    for name in ['billing.json','probe-freeze.txt','gpu-environment.txt','setup.log',
                 'fitting.log','refit.log','shieldstral-development.log','qwen-development.log',
                 'shieldstral-test.log','qwen-test.log','first-smoke-failure.log','initial-registration.json']:
        copy(work/name,Path('runtime')/name if name!='billing.json' else name)
    write(out/'runtime/cpu-environment.json',dict(python=platform.python_version(),platform=platform.platform(),
        packages={n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','threadpoolctl']}))
    for rel,h in freeze['sources'].items():
        copy(ROOT/rel,Path('source')/rel)
        if digest(out/'source'/rel)!=h:raise ValueError('Snapshot source differs')
    for sub in ['evals','evals/ensemble','evals/wildguard','evals/qwen_policy','evals/leaderboard']:
        copy(ROOT/sub/'__init__.py',Path('source')/sub/'__init__.py')
    for name in ['verify_shield_probe.py','restore_shield_probe_inputs.py','plot_shield_probe.py','report_shield_probe.py','summarize_shield_probe_runtime.py','package_shield_probe.py']:
        copy(ROOT/'tools'/name,Path('source/tools')/name)
    copy(ROOT/'tests/test_shield_probe.py','source/tests/test_shield_probe.py')
    for name in ['setup.sh','development.sh','test.sh','refit.py']:
        copy(work/name,Path('source/runtime')/name)
    for name in ['PLAN.md','NOTES.md','RUNNING.md','RESULTS.md','progress.json']:
        copy(ROOT/'docs/shield-probe'/name,name)
    for name in ['PLAN.md','RUNNING.md']:
        p=out/name
        text=p.read_text().replace('../research-directions/','../../docs/research-directions/').replace('../activation-probe/','../../docs/activation-probe/')
        p.write_text(text)
    text=(ROOT/'docs/shield-probe/README.md').read_text().replace('../leaderboard/METRICS.md','../../docs/leaderboard/METRICS.md').replace('../research-directions/','../../docs/research-directions/').replace('../activation-probe/','../../docs/activation-probe/')
    (out/'READOUT.md').write_text(text)
    for p in (ROOT/'docs/shield-probe/figures').glob('*'):
        copy(p,Path('figures')/p.name)
    result=read(state/'test-results.json')
    columns=['profile','method','candidate','threshold','n','balanced_accuracy','accuracy','macro_f1','mcc',
             'recall','specificity','false_positive_rate','false_negative_rate','false_blocks','missed_violations','unresolved']
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');writer.writeheader()
        for profile,rr in result['profiles'].items():
            for name,row in rr.items():
                if row is None:continue
                values=dict(profile=profile,method=name,candidate=row['candidate'],threshold=row['threshold'],**row['test'])
                writer.writerow({k:values[k] for k in columns})
    write(out/'provenance.json',dict(packaged_utc=now(),protocol_commit='7e148c7',pre_test_freeze_commit=read(ROOT/'docs/shield-probe/progress.json')['pre_test_freeze_commit'],
        current_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_root='source',private_artifacts_excluded=['source prompt text','pooled feature vectors','API and SSH credentials'],
        note='Up to 75 candidates; same frozen model/policy weights; one fixed harmfulness task. Historical controls used a different validation population.'))
    (out/'requirements.txt').write_text(''.join(n+'=='+importlib.metadata.version(n)+'\n'
        for n in ['numpy','scipy','scikit-learn','threadpoolctl']))
    (out/'README.md').write_text('''# Frozen-representation classifier study

[Readable findings](READOUT.md) · [Protocol](PLAN.md) · [All metrics](test-results.json) ·
[CSV](results.csv) · [Implementation notes](NOTES.md) · [Reproduction guide](RUNNING.md)

This immutable bundle tests Qwen3.5-4B and Shieldstral-1.0-3B representations on
WildGuard prompt harmfulness. The primary method concatenates their final-layer
features before supervised logistic regression. A separately registered secondary
search chooses earlier layers/pooling on validation. Language-model weights and
policy text stay frozen; the small classifiers are trained with labels.

The bundle includes all validation candidates, the pre-test freeze, fitted
coefficients/scalers, selected test outputs, operating profiles, confidence
intervals, source and runtime records. It contains no source prompts or pooled
embedding vectors. Restore authorized source inputs with the supplied utility
and regenerate private features to repeat fitting.

From this directory, with the listed CPU dependencies:

```sh
PYTHONPATH=source python3 -m evals.shield_probe.study reproduce --state .
PYTHONPATH=source python3 source/tools/verify_shield_probe.py --state .
```

These commands check saved outputs without GPU inference. The original private
cache also reproduced every candidate fit with identical coefficient arrays and
validation probabilities within a 1e-9 numerical tolerance; see
`refit-reproduction.json`. Full inference can
differ numerically across hardware/library versions. Match the recorded runtime
when attempting to regenerate features.

`feature-provenance/` records feature hashes, identities and runtime measurements;
it is not the feature cache. The first smoke failure and its pre-fit tokenizer-container repair are recorded
in the runtime log and implementation notes.
Published benchmark test results had been examined before this follow-up; its
new pre-test freeze does not make the public test a pristine blind evaluation.

The historical WildGuard and specialist-score-ensemble controls use the same
test prompts but their prior validation selections. They are context, not an
equal-search-budget causal comparison. This study has its own 1,536-row
validation protocol and is separate from the common-validation leaderboard.

Compute was terminated and billing reconciled; see [billing](billing.json).
Model and dataset references are in the protocol. Their publishers' terms remain
applicable. Checksums cover all immutable files except the checksum file itself.
''')
    write(out/'checksums.json',{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()})
    print('Packaged',out,'files',len(list(out.rglob('*'))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();package(a.state,a.out)
