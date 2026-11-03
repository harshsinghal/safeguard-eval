from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
TASKS = ('code', 'skills')
SEEDS = (20261103, 20261104, 20261105)
MODELS = {
    'jina-v2': dict(model='jinaai/jina-embeddings-v2-base-code',
        revision='516f4baf13dec4ddddda8631e019b5737c8bc250',
        code_revision='3baf9e3ac750e76e8edd3019170176884695fb94', dimension=768),
    'jina-code': dict(model='jinaai/jina-code-embeddings-0.5b',
        revision='4db235132dafbe56a8b9c5f59b59795ecf58a4a7', dimension=896),
    'qwen4': dict(model='Qwen/Qwen3.5-4B', revision='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'),
    'qwen9': dict(model='Qwen/Qwen3.5-9B', revision='c202236235762e1c871ad0ccb60c8ee5ba337b9a'),
}

def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
def hash_value(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text())
def write(path, x):
    path=Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(x, indent=2, ensure_ascii=False)+'\n')
def rows(path): return [json.loads(x) for x in Path(path).read_text().split('\n') if x.strip()]
def jsonl(path, rr):
    path=Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(canonical(r)+'\n' for r in rr))
def data(state, task, split):
    rr=rows(Path(state)/f'data/{task}/{split}.jsonl')
    if len({r['id'] for r in rr})!=len(rr): raise ValueError('Duplicate IDs')
    for r in rr:
        if hash_value(r['prompt'])!=r['prompt_sha256']: raise ValueError('Changed prompt')
    return rr
def meta(r): return {k:v for k,v in r.items() if k!='prompt'}
def predictions(rr, scores, model, config, **extra):
    if len(rr)!=len(scores): raise ValueError('Score alignment')
    out=[]
    for r,s in zip(rr,scores):
        s=float(s)
        if not math.isfinite(s) or not 0<=s<=1: raise ValueError('Invalid score')
        out.append({**meta(r), 'model':model, 'config':config, 'score':s,
                    'prediction':'BLOCK' if s>=.5 else 'ALLOW', **extra})
    return out
def measures(rr):
    from sklearn.metrics import f1_score, matthews_corrcoef
    if not rr: return {'n':0}
    y=[int(r['expected']=='BLOCK') for r in rr];p=[int(r['prediction']=='BLOCK') for r in rr]
    if any(r['prediction'] not in ('ALLOW','BLOCK') for r in rr): raise ValueError('Unresolved result')
    n0=y.count(0);n1=y.count(1);fp=sum(a==0 and b==1 for a,b in zip(y,p));fn=sum(a==1 and b==0 for a,b in zip(y,p))
    tpr=(n1-fn)/n1 if n1 else None;tnr=(n0-fp)/n0 if n0 else None
    return dict(n=len(rr),benign=n0,malicious=n1,accuracy=1-(fp+fn)/len(rr),
        balanced_accuracy=(tpr+tnr)/2 if n0 and n1 else None,
        macro_f1=float(f1_score(y,p,labels=[0,1],average='macro',zero_division=0)),
        mcc=float(matthews_corrcoef(y,p)),false_blocks=fp,missed_threats=fn,
        false_block_rate=fp/n0 if n0 else None,miss_rate=fn/n1 if n1 else None,
        recall=tpr,specificity=tnr,unresolved=0)
def sources():
    pp=list((ROOT/'evals/artifact_representations').glob('*.py'))
    pp += [ROOT/'docs/artifact-representations/PLAN.md']
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(pp)}
def verify(state, test=False):
    state=Path(state);reg=read(state/'registration.json')
    if reg['sources']!=sources(): raise ValueError('Source drift requires amendment')
    for p,h in reg['files'].items():
        if '/test.' in p and not test: continue
        if digest(state/p)!=h: raise ValueError('Registered input changed: '+p)
    if test:
        freeze=read(state/'freeze.json')
        if freeze['registration_sha256']!=digest(state/'registration.json'): raise ValueError('Freeze drift')
        for p,h in freeze['files'].items():
            if digest(state/p)!=h: raise ValueError('Selection drift: '+p)
    return reg
def complete(state, model, task, split, config):
    expected={r['id']:r for r in rows(Path(state)/f'metadata/{task}/{split}.jsonl')}
    rr=rows(Path(state)/f'predictions/{model}/{task}/{split}/{config}.jsonl')
    if len(rr)!=len(expected) or {r['id'] for r in rr}!=set(expected): raise ValueError('Missing/duplicate prediction')
    for r in rr:
        if any(r[k]!=expected[r['id']][k] for k in ('expected','group','prompt_sha256')): raise ValueError('Misalignment')
    return sorted(rr,key=lambda r:r['id'])
