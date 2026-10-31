"""Pinned components, identity checks, and artifact helpers."""
from pathlib import Path
import gzip
import hashlib
import json
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
SEED=20261031
PRIOR_SPEND=15.26540555656
POOL={'wildguard':['policylm','shieldstral','cope','qwen-4b','jev','kev','clef'],
      'hatexplain':['policylm','shieldstral','qwen-4b','jev','kev','clef']}
FAMILY={**{m:'specialist' for m in ['policylm','shieldstral','cope']},
        'qwen-4b':'general',**{m:'decision' for m in ['jev','kev','clef']}}
META=('id','expected','group','prompt_sha256','source_index','subcategory','adversarial','source_label','platform','agreement')
BASE='published_runs/2026-10-27-ensemble'
DEC='published_runs/2026-10-29-decision-models'
JEV='published_runs/2026-10-29-jev'
PROBE='published_runs/2026-10-30-shield-probe'
POLICY_IDS={'jev':'detailed','kev':'brief','clef':'examples'}


def now(): return datetime.now(timezone.utc).isoformat()
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def rows(p):
 p=Path(p)
 with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:return [json.loads(l) for l in f if l.strip()]
def write(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 data=(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 p.write_bytes(gzip.compress(data,mtime=0) if p.suffix=='.gz' else data)
def write_rows(p,rr):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 data=''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rr).encode()
 p.write_bytes(gzip.compress(data,mtime=0) if p.suffix=='.gz' else data)
def metadata(rr): return [{k:r[k] for k in META if k in r} for r in rr]
def sources(inference=False):
 own=['common.py','prepare.py','infer.py'] if inference else [p.name for p in (ROOT/'evals/smart_ensemble').glob('*.py')]
 paths=[ROOT/'evals/smart_ensemble'/p for p in own]
 paths += [ROOT/p for p in ['evals/decision_models/adapters.py','evals/decision_models/study.py','evals/decision_models/vendor-hashes.json','evals/jev/api.py','evals/ensemble/common.py','evals/leaderboard/metrics.py','docs/smart-ensemble/PLAN.md']]
 return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
def verify(state):
 reg=read(Path(state)/'registration.json')
 for p,h in reg['inference_sources'].items():
  if digest(ROOT/p)!=h:raise ValueError('Changed registered inference source: '+p)
 for p,h in reg['data_hashes'].items():
  if digest(Path(state)/p)!=h:raise ValueError('Changed registered data/policy: '+p)
 return reg

def align_scores(meta,rr):
 byid={r['id']:r for r in rr}
 if len(byid)!=len(rr) or set(byid)!={r['id'] for r in meta}:raise ValueError('Missing, additional or duplicate scores')
 out=[]
 for r in meta:
  o=byid[r['id']]
  for k in ['expected','group','prompt_sha256']:
   if k in o and o[k]!=r[k]:raise ValueError('Mismatched '+k)
  out.append({**r,**{k:o[k] for k in ['score','prediction','top_token_is_label'] if k in o}})
 return out

def archived_rows(ds,model,split):
 if model in ['jev','kev','clef']:
  middle='' if model=='jev' else model+'/'
  return f"{JEV if model=='jev' else DEC}/predictions/{middle}{ds}/{split}/{POLICY_IDS[model]}.jsonl.gz"
 if ds=='wildguard' and model=='qwen-4b':return f'{PROBE}/feature-provenance/qwen/{split}/records.json'
 return f'{BASE}/scores/{ds}/{model}/{split}.jsonl.gz'

def normalized_cached(ds,model,split,meta):
 path=ROOT/archived_rows(ds,model,split)
 if ds=='wildguard' and model=='qwen-4b':
  rr=[dict(id=r['id'],score=r['native_score'],prediction='ERROR' if r['native_score'] is None else ('BLOCK' if r['native_score']>=.5 else 'ALLOW'),top_token_is_label=r.get('top_token_is_label')) for r in read(path)]
 else:rr=rows(path)
 return align_scores(meta,rr)
