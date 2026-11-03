from pathlib import Path
import copy
import json
import gzip
import hashlib
from evals.prompt_injection.common import canonical, hash_value, digest as file_digest, read, rows, write, jsonl, now, measures
from evals.prompt_injection.common import MODELS as PREVIOUS_MODELS

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261102
TASKS = ('code', 'skills')
MODELS = {k: copy.deepcopy(PREVIOUS_MODELS[k]) for k in ('policylm','shieldstral','kev','clef','jev')}
MODELS['qwen'] = dict(model='Qwen/Qwen3.5-4B', revision='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a',
    decision='yes/no next-token-pair argmax; thinking disabled; BLOCK on tie')
ENCODER = dict(model='LiquidAI/LFM2.5-Encoder-350M', revision='b886781f7c6f10ca9b7096e21b83e30a073c2f39',
    seed=SEED, learning_rates=[2e-5,5e-5], epochs=3, max_length=8192, cutoff=.5)
VIEW_BYTES = 8000

def digest(path):
    path=Path(path)
    if not path.exists() and path.suffix=='.pt' and path.with_suffix('.pt.gz').is_file():
        # Hash the original checkpoint bytes, not their lossless storage wrapper.
        with gzip.open(path.with_suffix('.pt.gz'),'rb') as f:
            h=hashlib.sha256()
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        return h.hexdigest()
    return file_digest(path)

def rows(path):
    # Unicode U+2028/U+2029/NEL are valid inside JSON strings. They are not
    # record separators; splitlines() would corrupt adversarial artifact text.
    return [json.loads(line) for line in Path(path).read_text().split('\n') if line.strip()]

def view(text):
    """Same bounded, non-executable text view for every family. No label access."""
    raw = text.encode('utf-8')
    if len(raw) <= VIEW_BYTES:
        return text, False
    return (raw[:6000].decode('utf-8', errors='ignore') +
            '\n[... middle omitted by the benchmark input budget ...]\n' +
            raw[-2000:].decode('utf-8', errors='ignore')), True

def sources():
    paths = list((ROOT/'evals/malicious_artifacts').glob('*.py'))
    paths += [ROOT/p for p in ['docs/malicious-artifacts/PLAN.md','evals/prompt_injection/common.py',
        'evals/prompt_injection/infer.py','evals/retrieved_examples/native.py','evals/retrieved_examples/common.py',
        'evals/decision_models/adapters.py','evals/decision_models/study.py','evals/decision_models/vendor-hashes.json',
        'evals/run.py','evals/jev/api.py','evals/liquid_finetune/common.py','evals/liquid_finetune/runner.py',
        'evals/leaderboard/metrics.py']]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}

def verify(state, test=False):
    state=Path(state);reg=read(state/'registration.json')
    if reg['sources']!=sources():raise ValueError('Registered source changed; preserve an amendment')
    for p,h in reg['files'].items():
        if '/test.' in p and not test:continue
        if digest(state/p)!=h:raise ValueError('Registered data changed: '+p)
    if test:
        freeze=read(state/'freeze.json')
        if freeze['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Freeze changed')
        for p,h in freeze['files'].items():
            if digest(state/p)!=h:raise ValueError('Selection evidence changed: '+p)
    return reg

def load_data(state,task,split):
    rr=rows(Path(state)/f'data/{task}/{split}.jsonl')
    if len({r['id'] for r in rr})!=len(rr):raise ValueError('Duplicate ID')
    for r in rr:
        if hash_value(r['prompt'])!=r['prompt_sha256']:raise ValueError('Changed model input')
    return rr

def metadata(r):return {k:v for k,v in r.items() if k!='prompt'}

def complete(state,slug,task,split,pid):
    expected={r['id']:r for r in rows(Path(state)/f'metadata/{task}/{split}.jsonl')}
    rr=rows(Path(state)/f'predictions/{slug}/{task}/{split}/{pid}.jsonl')
    if len(rr)!=len(expected) or {r['id'] for r in rr}!=set(expected):raise ValueError('Incomplete predictions')
    for r in rr:
        if any(r[k]!=expected[r['id']][k] for k in ('expected','group','prompt_sha256')):raise ValueError('Misaligned predictions')
        if r['prediction'] not in ('ALLOW','BLOCK','ERROR'):raise ValueError('Invalid result')
    return sorted(rr,key=lambda r:r['id'])
