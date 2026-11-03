"""Align development populations without loading test score values."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
from .common import *
from evals.ensemble.common import assert_disjoint


def checked_archive(path,tracked):
 path=Path(path);archive=next(p for p in path.parents if p.parent==ROOT/'published_runs')
 checks=read(archive/'checksums.json');checks=checks.get('sha256',checks)
 rel=str(path.relative_to(archive));sha=digest(path)
 if checks[rel]!=sha:raise ValueError('Archived checksum mismatch: '+str(path))
 tracked[str(path.relative_to(ROOT))]=sha
 return sha


def prepare(state,work):
 state=Path(state);work=Path(work)
 if state.exists():raise ValueError('Use an unused state directory')
 state.mkdir(parents=True)
 hashes={};orig={};test_sources={};summaries={};configs={}
 def add(p,obj,is_rows=False):
  (write_rows if is_rows else write)(state/p,obj);hashes[p]=digest(state/p)
 manifest=read(ROOT/BASE/'data-manifest.json')
 for ds,names in POOL.items():
  metas={};summaries[ds]={};configs[ds]={}
  for split in ['fit','validation']:
   ref=ROOT/BASE/'scores'/ds/'policylm'/(split+'.jsonl.gz')
   checked_archive(ref,orig);meta=metadata(rows(ref));metas[split]=meta
   assert len(meta)=={'fit':4096,'validation':1536}[split]
   add(f'metadata/{ds}/{split}.jsonl.gz',meta,True)
   private=work/('shield-probe-run/state/inputs' if ds=='wildguard' else 'ensemble-run/state/data/hatexplain')/(split+'.jsonl')
   rr=rows(private);byid={r['id']:r for r in rr}
   if set(byid)!={r['id'] for r in meta}:raise ValueError('Private prompt population differs')
   inputs=[]
   for r in meta:
    p=byid[r['id']]['prompt']
    if hashlib.sha256(p.encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Prompt hash mismatch')
    inputs.append(dict(id=r['id'],prompt=p,prompt_sha256=r['prompt_sha256']))
   add(f'inputs/{ds}/{split}.jsonl',inputs,True)
   summaries[ds][split]=dict(n=len(meta),groups=len({r['group'] for r in meta}),labels=dict(Counter(r['expected'] for r in meta)))
   for model in names:
    if model in ['jev','kev','clef']:continue
    p=ROOT/archived_rows(ds,model,split);checked_archive(p,orig)
    add(f'scores/{ds}/{model}/{split}.jsonl.gz',normalized_cached(ds,model,split,meta),True)
  # These archived populations carry identities only, never model scores.
  private_test=work/('policy-transfer-run/state/data' if ds=='wildguard' else 'hatexplain-run/state/data')/'test.jsonl'
  tm=metadata(rows(private_test));tm=sorted(tm,key=lambda r:r['id'])
  assert len(tm)=={'wildguard':1699,'hatexplain':1924}[ds]
  add(f'metadata/{ds}/test.jsonl.gz',tm,True)
  assert_disjoint(metas['fit'],metas['validation'],tm)
  # Earlier decision-policy authoring/selection populations must be excluded.
  old=[]
  for split in ['fit','validation']:
   p=ROOT/JEV/'predictions'/ds/split/'brief.jsonl.gz';checked_archive(p,orig);old+=metadata(rows(p))
  for split in ['fit','validation']:
   assert_disjoint(metas[split],old)
  summaries[ds]['prior_decision_development_groups_excluded']=len({r['group'] for r in old})
  summaries[ds]['test']=dict(n=len(tm),groups=len({r['group'] for r in tm}),labels=dict(Counter(r['expected'] for r in tm)))
  for model in names:
   p=ROOT/archived_rows(ds,model,'test');test_sources[f'{ds}/{model}']=dict(path=str(p.relative_to(ROOT)),sha256=checked_archive(p,orig))
   if model in ['jev','kev','clef']:
    p=(ROOT/JEV/'policies'/ds/'final.json') if model=='jev' else (ROOT/DEC/'policies'/model/ds/'final.json')
    checked_archive(p,orig)
    prior=work/('jev-run' if model=='jev' else 'decision-models-run/state')
    rel=f'policies/{ds}/final.json' if model=='jev' else f'policies/{model}/{ds}/final.json'
    private=prior/rel
    old_freeze=read(prior/('policies-freeze.json' if model=='jev' else model+'/policies-freeze.json'))
    expected=old_freeze['policy_hashes'][ds] if model=='jev' else old_freeze['policies'][rel]
    if digest(private)!=expected:raise ValueError('Original private policy pack changed')
    pack=read(private);policy=pack[POLICY_IDS[model]]
    add(f'policies/{ds}/{model}.json',policy)
    if model=='jev':add(f'policies/{ds}/jev-pack.json',pack)
    configs[ds][model]=dict(policy=POLICY_IDS[model],policy_sha256=digest(state/f'policies/{ds}/{model}.json'),archive=str(p.relative_to(ROOT)))
   elif ds=='wildguard' and model=='qwen-4b':
    p=ROOT/PROBE/'policy.json';checked_archive(p,orig);add(f'policies/{ds}/{model}.json',read(p))
    configs[ds][model]=dict(policy='wg-p4-shieldstral-taxonomy-priority',revision='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a',adapter='HF frozen native conditional B/A; no representation classifier',policy_sha256=digest(p))
   else:
    conf=manifest['policies'][ds+'/'+model];configs[ds][model]=conf
    pp=ROOT/BASE/'policies'/ds/((model if ds=='wildguard' else conf['policy_id'])+'.json')
    if digest(pp)!=conf['sha256']:raise ValueError('Policy manifest hash mismatch')
    checked_archive(pp,orig);add(f'policies/{ds}/{model}.json',read(pp))
  # Canary cases are from OLD validation, not new fit, validation or test.
  original=rows(work/'jev-run/data'/ds/'validation.jsonl')
  ordered=sorted(original,key=lambda r:(len(r['prompt']),r['id']))
  sample=[ordered[round(i*(len(ordered)-1)/15)] for i in range(16)]
  add(f'inputs/{ds}/canary.jsonl',[{k:r[k] for k in ['id','prompt','prompt_sha256']} for r in sample],True)
  add(f'metadata/{ds}/canary.jsonl.gz',metadata(sample),True)
  for model in ['jev','kev','clef']:
   p=ROOT/archived_rows(ds,model,'validation');checked_archive(p,orig)
   old_by_id={r['id']:r for r in rows(p)}
   add(f'canary-reference/{ds}/{model}.jsonl.gz',[old_by_id[r['id']] for r in sample],True)
 write(state/'registration.json',dict(created_utc=now(),protocol_sha256=digest(ROOT/'docs/smart-ensemble/PLAN.md'),inference_sources=sources(True),data_hashes=hashes,original_hashes=orig,test_sources=test_sources,populations=summaries,components=configs,pool=POOL,seed=SEED,prior_spend_usd=PRIOR_SPEND,max_new_api_usd=1,max_new_gpu_usd=2.4,cumulative_cap_usd=20,prior_data_manifest_sha256=digest(ROOT/BASE/'data-manifest.json')))
 shutil.copy2(ROOT/'docs/smart-ensemble/PLAN.md',state/'PLAN.md')
 print(json.dumps(summaries,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--state',required=True);ap.add_argument('--work',required=True);a=ap.parse_args();prepare(a.state,a.work)
