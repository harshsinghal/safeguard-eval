"""Build a local prompt-free evidence package using an explicit file allowlist."""
import argparse
from pathlib import Path
import shutil

from evals.ensemble.common import ROOT, COHORTS, digest, read, write, now
from evals.ensemble.study import verify_freeze


def checksums(destination):
    destination=Path(destination)
    write(destination/'checksums.json',dict(created_utc=now(),sha256={str(p.relative_to(destination)):digest(p)
        for p in sorted(destination.rglob('*')) if p.is_file() and p.name!='checksums.json' and '__pycache__' not in p.parts}))


def export(state,destination):
    state,destination=Path(state),Path(destination)
    if destination.exists():raise ValueError('Evidence destination already exists')
    for cohort in COHORTS:verify_freeze(state,cohort)
    destination.mkdir(parents=True)
    def copy(source,relative):
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for name in ['data-manifest.json','inference-registration.json','ingestion.json','descriptive-comparison.json']:
        copy(state/name,name)
    for folder in ['scores','policies','cohorts']:
        for source in sorted((state/folder).rglob('*')):
            if source.is_file():copy(source,source.relative_to(state))
    # Raw requests/responses, private data, credentials, and operational SSH files are excluded.
    for source in sorted((state/'new-runs').glob('*/*/*')):
        if source.name in ['manifest.json','completion.json','rendered-policy.json']:
            copy(source,source.relative_to(state))
    for name in ['environment.txt','policy-freeze.txt','vllm-freeze.txt']:
        copy(state/'runtime'/name,Path('runtime')/name)
    copy(state.parent/'billing.json','billing.json')
    for source in sorted((ROOT/'evals/ensemble').glob('*.py')):
        copy(source,Path('source/evals/ensemble')/source.name)
    copy(ROOT/'evals/__init__.py','source/evals/__init__.py')
    copy(ROOT/'tests/test_ensemble.py','source/tests/test_ensemble.py')
    copy(ROOT/'docs/ensemble/PLAN.md','PLAN.md')
    registration=read(state/'inference-registration.json')
    for relative,expected in registration['sources'].items():
        source=ROOT/relative
        if digest(source)!=expected:raise ValueError('Registered inference source changed: '+relative)
        copy(source,Path('inference-source')/relative)
    for name in ['setup.sh','prefetch.py']:
        copy(state.parent/name,Path('runtime')/name)
    (destination/'requirements.txt').write_text('numpy==2.4.6\nscipy==1.17.1\nscikit-learn==1.9.1\njoblib==1.6.0\nthreadpoolctl==3.7.0\nmatplotlib==3.11.2\n')
    checksums(destination)
    print('Exported prompt-free evidence:',destination)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();export(a.state,a.destination)
