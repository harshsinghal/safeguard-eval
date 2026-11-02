"""Shared contracts. No threshold fitting or score calibration in this study."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MODELS={
    'policylm':dict(model='musubilabs/policylm-1.7b',revision='b3b2cd408a08a68ab6a30c1fc1e440204e44d57e',
        decision='publisher precision preset, fixed 0.335',clean=True,max_chars=None,max_batch_rows=1),
    'shieldstral':dict(model='mistralai/Shieldstral-1.0-3B',revision='003ec7e2b0bab5f0e6307edbaf186fa5822b76f5',
        decision='yes/no token-pair argmax, BLOCK on tie'),
    'safeguard':dict(model='openai/gpt-oss-safeguard-20b',provider='Groq via OpenRouter',
        decision='generated binary JSON label',reasoning='medium',max_tokens=2048,
        revision='provider alias; immutable checkpoint not exposed'),
    'kev':dict(model='jaredpalmer/kev-4b',revision='6cfce5c2fa4b4bd64026336ab649c5ca78857d52',
        code_revision='2074cc44256200bb37540103fa4572901faa10f3',
        base='Qwen/Qwen3.5-4B-Base',base_revision='1001bb4d826a52d1f399e183466143f4da7b741b',
        decision='native Choice argmax, ALLOW on tie; publisher learned temperature retained'),
    'clef':dict(model='Cloudflare/clef-flash',revision='f0b7d3cd65296abfe459e6c228b618f5d8b26d2f',
        decision='native Choice argmax, ALLOW on tie'),
    'jev':dict(model='typesafe/jev-1.14',resolved='typesafe/jev-1.14-20261014',provider='TypeSafe via OpenRouter',
        decision='native Choice argmax'),
}

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def hash_value(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def write(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def jsonl(path,values):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(canonical(r)+'\n' for r in values))

def sources():
    pp=list((ROOT/'evals/prompt_injection').glob('*.py'))+[ROOT/'docs/prompt-injection/PLAN.md']
    pp += [ROOT/p for p in ('evals/run.py','evals/retrieved_examples/native.py',
        'evals/retrieved_examples/common.py','evals/decision_models/adapters.py',
        'evals/decision_models/study.py','evals/decision_models/vendor-hashes.json',
        'evals/jev/api.py','evals/leaderboard/metrics.py')]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(pp)}

def verify(state,test=False):
    state=Path(state);r=read(state/'registration.json')
    if r['sources']!=sources():raise ValueError('Source changed after registration; document an amendment')
    for path,h in r['files'].items():
        if not test and path in ('data/test.jsonl','metadata/test.jsonl') and not (state/path).exists():continue
        if digest(state/path)!=h:raise ValueError('Registered input changed: '+path)
    if test:
        f=read(state/'freeze.json')
        if f['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Registration changed after selection')
        for p,h in f['files'].items():
            if digest(state/p)!=h:raise ValueError('Selection evidence changed: '+p)
    return r

def measures(records):
    from evals.leaderboard.metrics import metrics
    m=metrics([int(r['expected']=='BLOCK') for r in records],
        [{'ALLOW':0,'BLOCK':1,'ERROR':-1}[r['prediction']] for r in records])
    if not m['positives'] or not m['negatives']:
        for k in ('macro_f1','block_f1','allow_f1','mcc'):m[k]=None
    return m

def completed(state,slug,split,pid):
    expected={r['id']:r for r in rows(Path(state)/'metadata'/f'{split}.jsonl')}
    records=rows(Path(state)/'predictions'/slug/split/(pid+'.jsonl'))
    if len(records)!=len(expected) or {r['id'] for r in records}!=set(expected):raise ValueError('Incomplete predictions')
    for r in records:
        if any(r[k]!=expected[r['id']][k] for k in ('expected','group','split','prompt_sha256')):
            raise ValueError('Misaligned prediction')
        if r['prediction'] not in ('ALLOW','BLOCK','ERROR'):raise ValueError('Invalid prediction')
    return sorted(records,key=lambda r:r['id'])
