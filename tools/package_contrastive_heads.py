"""Publish evidence without source text, embeddings, provider keys or credentials."""
import argparse
import importlib.metadata
import platform
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.contrastive_heads.common import *

def package(state,out):
    state,out=Path(state).resolve(),Path(out).resolve();f=check_freeze(state)
    billing=read(state/'billing.json')
    if billing['status']!='terminated' or billing['cumulative_accounted_usd']>20:raise ValueError('Unclosed resources or budget')
    out.mkdir(parents=True,exist_ok=False)
    def copy(src,relative):
        dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    for name in ['registration.json','registration-v1.json','PLAN.md','AMENDMENTS.md','RUN-LOG.md',
        'freeze.json','results.json','test-predictions.json','verification.json','billing.json','gpu-billing.json','progress.json']:
        copy(state/name,name)
    for sub in ['metadata','policies']:
        for p in (state/sub).rglob('*'):
            if p.is_file():copy(p,p.relative_to(state))
    for ds in DATASETS:
        for backend in BACKENDS:
            folder=state/'fits'/ds/backend;v=read(folder/'validation.json')
            for name in ['validation.json','scaler.npz']:copy(folder/name,folder.relative_to(state)/name)
            # Every candidate's hashes and outputs are public; distribute the
            # predeclared primary-seed balanced classifier weights for deployment.
            for head,cc in v['choices'].items():
                name=v['candidates'][cc['balanced']['candidate']]['parameters'][0]
                copy(state/name,name)
    for p in (state/'features').rglob('*.json'):
        copy(p,Path('feature-provenance')/p.relative_to(state/'features'))
    for rel,h in f['sources'].items():
        copy(ROOT/rel,Path('source')/rel)
        if digest(out/'source'/rel)!=h:raise ValueError('Frozen source mismatch')
    for sub in ['evals','evals/ensemble','evals/activation_probe','evals/hatexplain','evals/leaderboard']:
        copy(ROOT/sub/'__init__.py',Path('source')/sub/'__init__.py')
    for name in ['report_contrastive_heads.py','plot_contrastive_heads.py','verify_contrastive_heads.py','package_contrastive_heads.py']:
        copy(ROOT/'tools'/name,Path('source/tools')/name)
    copy(ROOT/'tests/test_contrastive_heads.py','source/tests/test_contrastive_heads.py')
    for p in (state/'runtime').iterdir():
        if p.is_file():copy(p,Path('runtime')/p.name)
    for name in ['RESULTS.md','results.csv','RUNNING.md']:
        copy(ROOT/'docs/contrastive-heads'/name,name)
    for p in (ROOT/'docs/contrastive-heads/figures').iterdir():copy(p,Path('figures')/p.name)
    cpu=dict(python=platform.python_version(),platform=platform.platform(),packages={n:importlib.metadata.version(n) for n in ['torch','numpy','scipy','scikit-learn','threadpoolctl']})
    write(out/'runtime/cpu-environment.json',cpu)
    (out/'requirements.txt').write_text(''.join(n+'=='+v+'\n' for n,v in cpu['packages'].items()))
    write(out/'provenance.json',dict(packaged_utc=now(),protocol_commit='41f5e5c',amendment_commit='53527ec',
        pre_test_freeze_commit=read(state/'progress.json')['pre_test_freeze_commit'],
        full_private_parameter_inventory=f['hashes'],public_parameter_scope='Primary seed, balanced profile; other weights remain private.',
        private_exclusions=['submitted text','frozen feature arrays','credentials'],
        verification='All 164 candidate checkpoints independently refitted; published metric/selection verification requires no GPU.'))
    (out/'README.md').write_text('''# Frozen features and contrastive task classifiers

[Readable study](../../docs/contrastive-heads/README.md) · [All results](RESULTS.md) ·
[CSV](results.csv) · [Protocol](PLAN.md) · [Amendment](AMENDMENTS.md) · [Reproduction](RUNNING.md)

PolicyLM 1.7B and ModernBERT-base representations are frozen. Small logistic,
ordinary neural and contrastive neural classifiers are trained separately for
WildGuard prompt harmfulness and HateXplain hate detection. No backbone is
fine-tuned. Both official tests have been used in earlier studies.

This bundle preserves every validation candidate, all four operating profiles,
all three selected neural training seeds, test predictions, paired intervals,
frozen configuration and parameter hashes, primary balanced classifier weights,
input identities, feature provenance, source, runtime and billing evidence.
Source text and embeddings are excluded. Remaining checkpoint weights are in
the author's private run directory; their hashes and predictions are included.

Verify a copy of this bundle without GPU/API calls:

```sh
PYTHONPATH=source python3 source/tools/verify_contrastive_heads.py --state .
```

The verifier writes a fresh verification.json; use a copy to preserve the original
checksums. requirements.txt records the CPU runtime. Independent refitting also
requires the private feature arrays or reproducing their extraction.

The generic RUNNING.md links point into the repository docs directory; consult
the live [reproduction guide](../../docs/contrastive-heads/RUNNING.md) for those
parent-study and dataset links. All package files except checksums.json itself
are listed in checksums.json.
''')
    write(out/'checksums.json',{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()})
    print('PACKAGED',out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True);package(**vars(p.parse_args()))
