"""Shared identities and strict score alignment; never infer labels from failures."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261027
PRIOR_SPEND = 12.12119753456
CAP = 20.0
WG = ROOT / 'published_runs/2026-10-24-wildguard'
HX = ROOT / 'published_runs/2026-10-26-hatexplain'
WG_RUNS = {'policylm': 'p4', 'shieldstral': 'p4', 'cope': 'p3'}
HX_POLICIES = {'policylm': 'p0', 'shieldstral': 'shieldstral-p2', 'qwen-4b': 'qwen-4b-p1'}
COHORTS = {'wildguard-specialists': ('wildguard', ['policylm', 'shieldstral', 'cope']),
           'hatexplain-specialists': ('hatexplain', ['policylm', 'shieldstral']),
           'hatexplain-mixed': ('hatexplain', ['policylm', 'shieldstral', 'qwen-4b'])}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, value, exclusive=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def write_rows(path, values):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = ''.join(json.dumps(v, ensure_ascii=False, allow_nan=False) + '\n' for v in values).encode()
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)


def source_hashes():
    paths = list((ROOT / 'evals/ensemble').glob('*.py'))
    paths += [ROOT / 'evals/hatexplain'/n for n in ['policy.py','run.py','orchestrate.py','common.py']]
    paths += [ROOT/'evals/wildguard/run.py', ROOT/'evals/qwen_policy/run.py', ROOT/'evals/run.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def assert_disjoint(*populations):
    seen_ids, seen_groups, seen_hashes = set(), set(), set()
    for population in populations:
        ids = [r['id'] for r in population]
        groups = {r['group'] for r in population}
        hashes = {r['prompt_sha256'] for r in population}
        if len(ids) != len(set(ids)) or set(ids) & seen_ids or groups & seen_groups or hashes & seen_hashes:
            raise ValueError('Duplicate or leaking development populations')
        seen_ids.update(ids); seen_groups.update(groups); seen_hashes.update(hashes)


def align(predictions, names):
    """Only named numeric scores become features; metadata and labels are separate."""
    import numpy as np
    indexes = {}
    for name in names:
        rr = predictions[name]
        index = {r['id']: r for r in rr}
        if len(index) != len(rr) or not rr:
            raise ValueError('Empty or duplicate prediction population')
        indexes[name] = index
    keys = set(indexes[names[0]])
    if any(set(v) != keys for v in indexes.values()):
        raise ValueError('Model populations differ; do not inner-join away missing cases')
    meta, features, valid = [], [], []
    for identifier in sorted(keys):
        ref = indexes[names[0]][identifier]
        values, good = [], []
        for name in names:
            r = indexes[name][identifier]
            if any(r.get(k) != ref.get(k) for k in ('expected','group','prompt_sha256','source_label','adversarial','subcategory')):
                raise ValueError('Mismatched content, labels or groups')
            score = r.get('score')
            if r['prediction'] == 'ERROR':
                values.append(0.5); good.append(False)
            elif not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError('Missing or invalid numerical score')
            else:
                values.append(float(score)); good.append(True)
        if ref['expected'] not in ('ALLOW', 'BLOCK'):
            raise ValueError('Unknown target')
        meta.append({k:v for k,v in ref.items() if k not in ('prediction','score','usage','latency_seconds','request_sha256','error_type','prompt')})
        features.append(values); valid.append(good)
    return meta, np.asarray(features), np.asarray([r['expected']=='BLOCK' for r in meta],dtype=int), np.asarray(valid)


def partition(rows_in, fit_n=4096, val_n=1536):
    """Deterministic proportional sampling with intact duplicate groups."""
    grouped = defaultdict(list)
    for r in rows_in: grouped[r['group']].append(r)
    if len(rows_in) < fit_n + val_n:
        fit_n = int(len(rows_in)*.75); val_n = len(rows_in)-fit_n
    def select(available, target, salt):
        buckets = defaultdict(list)
        for group, members in available.items():
            stratum = Counter(r.get('source_label',r['expected']) for r in members).most_common(1)[0][0]
            buckets[stratum].append((group,members))
        total = sum(len(v) for v in available.values())
        quotas = {k: int(target * sum(len(v) for _,v in b)/total) for k,b in buckets.items()}
        for k in sorted(buckets)[:target-sum(quotas.values())]: quotas[k]+=1
        chosen=[]; selected=set()
        for label,bucket in sorted(buckets.items()):
            count=0
            for group,members in sorted(bucket,key=lambda x:hashlib.sha256(f'{SEED}:{salt}:{x[0]}'.encode()).hexdigest()):
                if count+len(members)<=quotas[label]:
                    chosen.extend(members);selected.add(group);count+=len(members)
        return sorted(chosen,key=lambda r:r['id']), {g:v for g,v in available.items() if g not in selected}
    fit, rest = select(grouped,fit_n,'fit')
    validation, _ = select(rest,val_n,'validation')
    assert_disjoint(fit,validation)
    if min(len(fit),len(validation))<256: raise ValueError('Insufficient independent development data')
    return fit, validation


def metrics(meta, predictions, scores=None):
    import numpy as np
    y = np.array([r['expected']=='BLOCK' for r in meta]); p=np.asarray(predictions)
    tp=int(((p==1)&y).sum());tn=int(((p==0)&~y).sum())
    fp=int((~y&(p!=0)).sum());fn=int((y&(p!=1)).sum())
    f=lambda a,b: a/b if b else 0.
    result=dict(n=len(y),accuracy=(tp+tn)/len(y),macro_f1=(f(2*tp,2*tp+fp+fn)+f(2*tn,2*tn+fp+fn))/2,
        violation_f1=f(2*tp,2*tp+fp+fn),violation_recall=f(tp,tp+fn),false_blocks=int((~y&(p==1)).sum()),
        missed_violations=fn,errors=int((p==-1).sum()),
        confusion={'ALLOW':{'ALLOW':tn,'BLOCK':int((~y&(p==1)).sum()),'ERROR':int((~y&(p==-1)).sum())},
                   'BLOCK':{'ALLOW':int((y&(p==0)).sum()),'BLOCK':tp,'ERROR':int((y&(p==-1)).sum())}})
    if scores is not None and not (p==-1).any():
        s=np.clip(np.asarray(scores),1e-7,1-1e-7)
        result.update(brier=float(np.mean((s-y)**2)),log_loss=float(-np.mean(y*np.log(s)+(1-y)*np.log(1-s))))
    return result
