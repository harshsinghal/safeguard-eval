"""Create a self-contained local archive of scores and CPU-only learned artifacts."""
import argparse
from pathlib import Path
import shutil

from evals.ensemble.common import ROOT,COHORTS,digest,write,now
from evals.ensemble_logits.study import verify_freeze,verify_test_stage


def checksums(folder):
    folder=Path(folder)
    write(folder/'checksums.json',dict(created_utc=now(),sha256={str(p.relative_to(folder)):digest(p)
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='checksums.json' and '__pycache__' not in p.parts}))


def export(state,destination):
    state,destination=Path(state),Path(destination)
    if destination.exists():raise ValueError('Destination exists')
    for cohort in COHORTS:verify_freeze(state,cohort)
    verify_test_stage(state)
    shutil.copytree(state,destination)
    def copy(source,relative):
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for relative in ['evals/__init__.py','evals/ensemble/__init__.py','evals/ensemble/common.py','evals/ensemble/learn.py','evals/ensemble/study.py']:
        copy(ROOT/relative,Path('source')/relative)
    for source in (ROOT/'evals/ensemble_logits').glob('*.py'):
        copy(source,Path('source/evals/ensemble_logits')/source.name)
    copy(ROOT/'tests/test_ensemble_logits.py','source/tests/test_ensemble_logits.py')
    copy(ROOT/'docs/ensemble-logits/PLAN.md','source/docs/ensemble-logits/PLAN.md')
    copy(ROOT/'published_runs/2026-10-27-ensemble/requirements.txt','requirements.txt')
    checksums(destination)
    print('Exported CPU-only log-odds evidence:',destination)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();export(a.state,a.destination)
