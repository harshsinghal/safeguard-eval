"""Fit, freeze, evaluate and reproduce the cross-family score ensemble."""
import argparse
from pathlib import Path
import shutil
import platform
import csv
import numpy as np
import scipy
import sklearn
import joblib
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits
from .common import *
from .learn import fit_methods,predict,describe,EPS
from evals.ensemble.common import align,assert_disjoint
from evals.leaderboard.metrics import select,decisions,metrics,bootstrap,interval,eligible,PROFILES


def population(state,ds,split):
 meta=rows(state/f'metadata/{ds}/{split}.jsonl.gz');by={}
 for model in POOL[ds]:by[model]=align_scores(meta,rows(state/f'scores/{ds}/{model}/{split}.jsonl.gz'))
 meta,x,y,valid=align(by,POOL[ds]);meta=metadata(meta)
 look={m:{r['id']:r for r in rr} for m,rr in by.items()}
 native=np.array([[{'ALLOW':0,'BLOCK':1,'ERROR':-1}[look[m][r['id']]['prediction']] for m in POOL[ds]] for r in meta])
 return meta,x,y,valid,native


def train_one(state,ds):
 tm,x,y,ok,n=population(state,ds,'fit');vm,v,vy,vok,vn=population(state,ds,'validation')
 assert_disjoint(tm,vm)
 with threadpool_limits(limits=1):models,info=fit_methods(POOL[ds],x,y,ok,n,[r['group'] for r in tm])
 outputs={k:predict(c,v,vok,vn) for k,c in models.items()}
 selections={k:select(vy,{k:o})[0] for k,o in outputs.items()}
 selections['best-individual']=select(vy,{k:o for k,o in outputs.items() if k.startswith('single/')})[0]
 return models,info,dict(metadata=vm,outputs=outputs),selections


def fit(state):
 state=Path(state);verify(state)
 if (state/'freeze.json').exists():raise ValueError('Already frozen; use reproduce')
 all_models={};summary={};validation={};selected={}
 for ds in POOL:
  print('FITTING',ds,flush=True)
  all_models[ds],summary[ds],validation[ds],selected[ds]=train_one(state,ds)
  print('SELECTED',ds,summary[ds]['parameters']['primary']['names'],selected[ds]['primary']['balanced']['threshold'],flush=True)
 joblib.dump(all_models,state/'models.joblib',compress=3)
 write(state/'fitting.json',summary);write(state/'selection.json',selected)
 write(state/'validation-predictions.json.gz',validation)
 artifacts={}
 for p in sorted((state/'metadata').rglob('*.gz')):artifacts[str(p.relative_to(state))]=digest(p)
 for p in sorted((state/'scores').rglob('*.gz')):
  if p.name in ['fit.jsonl.gz','validation.jsonl.gz']:artifacts[str(p.relative_to(state))]=digest(p)
 for rel in ['registration.json','PLAN.md','AMENDMENTS.md','models.joblib','fitting.json','selection.json','validation-predictions.json.gz','jev-refresh-required.json']:
  artifacts[rel]=digest(state/rel)
 ss=sources();ss['docs/smart-ensemble/AMENDMENTS.md']=digest(ROOT/'docs/smart-ensemble/AMENDMENTS.md')
 write(state/'freeze.json',dict(created_utc=now(),protocol_sha256=digest(state/'PLAN.md'),artifacts=artifacts,sources=ss,primary='primary',selection_objective='balanced_accuracy',test_status='Outputs not yet evaluated; Jev test not yet requested',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,joblib=joblib.__version__),limits='Public tests already examined by this project; new supervised combination only'))
 (state/'requirements.txt').write_text(f'numpy=={np.__version__}\nscipy=={scipy.__version__}\nscikit-learn=={sklearn.__version__}\njoblib=={joblib.__version__}\nthreadpoolctl==3.6.0\n')
 print('FROZEN before final test scoring',flush=True)


def check_freeze(state):
 state=Path(state);f=read(state/'freeze.json')
 for rel,h in f['artifacts'].items():
  if digest(state/rel)!=h:raise ValueError('Frozen artifact changed: '+rel)
 for rel,h in f['sources'].items():
  if digest(ROOT/rel)!=h:raise ValueError('Frozen source changed: '+rel)
 return f


def summarize(meta,outputs,selections):
 y=np.array([r['expected']=='BLOCK' for r in meta],dtype=int);results={};preds={}
 for method,profiles in selections.items():
  results[method]={}
  for profile,choice in profiles.items():
   if choice is None:results[method][profile]=None;continue
   out=outputs[choice['candidate']];p=decisions(out,choice['threshold']);score=out['score'];m=metrics(y,p,score)
   good=p!=-1;ss=np.array([.5 if v is None else v for v in score])
   if good.any():m.update(brier=float(np.mean((ss[good]-y[good])**2)),log_loss=float(log_loss(y[good],ss[good],labels=[0,1])))
   record=dict(candidate=choice['candidate'],threshold=choice['threshold'],validation_metrics=choice['metrics'],metrics=m,test_target_met=eligible(m,profile),slices={})
   if profile=='balanced':
    for field in ['subcategory','adversarial','source_label','platform','agreement']:
     if any(field in r for r in meta):
      record['slices'][field]={}
      for value in sorted({str(r.get(field)) for r in meta}):
       ix=np.array([str(r.get(field))==value for r in meta]);record['slices'][field][value]=metrics(y[ix],p[ix])
   results[method][profile]=record;preds[method+'/'+profile]=p
 draws=bootstrap(meta,preds)
 for method,profiles in results.items():
  for profile,record in profiles.items():
   if record:record['ci95']={k:interval(a) for k,a in draws[method+'/'+profile].items()}
 primary=preds['primary/balanced'];pairs=[]
 for method in results:
  if method=='primary':continue
  key=method+'/balanced';other=preds[key]
  a=results['primary']['balanced']['metrics'];b=results[method]['balanced']['metrics']
  pairs.append(dict(a='primary',b=method,balanced_accuracy_difference=a['balanced_accuracy']-b['balanced_accuracy'],ci95=interval(draws['primary/balanced']['balanced_accuracy']-draws[key]['balanced_accuracy']),corrected=int(((primary==y)&(other!=y)).sum()),introduced=int(((primary!=y)&(other==y)).sum()),false_blocks_difference=a['false_blocks']-b['false_blocks'],misses_difference=a['missed_violations']-b['missed_violations'],both_error_rates_lower=a['compliant_error_rate']<b['compliant_error_rate'] and a['violation_error_rate']<b['violation_error_rate']))
 return dict(n=len(y),positives=int(y.sum()),negatives=int((y==0).sum()),methods=results,paired_comparisons=pairs)


def evaluate(state):
 state=Path(state);check_freeze(state)
 if (state/'results.json').exists():raise ValueError('Final results already exist; use reproduce')
 reg=read(state/'registration.json');fitted=joblib.load(state/'models.joblib');selections=read(state/'selection.json');test_outputs={};results={}
 for ds,names in POOL.items():
  meta=rows(state/f'metadata/{ds}/test.jsonl.gz')
  for m in names:
   if m=='jev':
    p=state/f'scores/{ds}/{m}/test.jsonl.gz'
    if not p.exists():raise ValueError('Fresh Jev test outputs required after freeze')
   else:
    src=reg['test_sources'][ds+'/'+m]
    if digest(ROOT/src['path'])!=src['sha256']:raise ValueError('Changed archived test scores')
    write_rows(state/f'scores/{ds}/{m}/test.jsonl.gz',normalized_cached(ds,m,'test',meta))
  tm,x,y,ok,n=population(state,ds,'test')
  assert_disjoint(rows(state/f'metadata/{ds}/fit.jsonl.gz'),rows(state/f'metadata/{ds}/validation.jsonl.gz'),tm)
  out={k:predict(c,x,ok,n) for k,c in fitted[ds].items()}
  test_outputs[ds]=dict(metadata=tm,outputs=out);results[ds]=summarize(tm,out,selections[ds])
  print('RESULT',ds,results[ds]['methods']['primary']['balanced']['metrics'],flush=True)
 write(state/'test-predictions.json.gz',test_outputs)
 write(state/'results.json',dict(created_utc=now(),datasets=results,uncertainty='2000 paired duplicate-group bootstrap draws; unadjusted, conditional on outputs; excludes search and API variability',primary='Training-OOF-selected logistic ensemble',added_training='Small supervised classifiers only; language-model weights and policies frozen'))
 write(state/'evaluation.json',dict(created_utc=now(),freeze_sha256=digest(state/'freeze.json'),test_hashes={str(p.relative_to(state)):digest(p) for p in (state/'scores').rglob('test.jsonl.gz')},results_sha256=digest(state/'results.json')))
 from .report import render
 render(state)


def reproduce(state):
 state=Path(state);check_freeze(state);saved=read(state/'fitting.json');choices=read(state/'selection.json');vp=read(state/'validation-predictions.json.gz');tp=read(state/'test-predictions.json.gz');checks={}
 for ds in POOL:
  models,info,validation,selection=train_one(state,ds)
  if selection!=choices[ds]:raise ValueError('Selection failed reproduction')
  if info['parameters']!=saved[ds]['parameters'] or info['paths']!=saved[ds]['paths']:raise ValueError('Fitted parameters/selection path differ')
  maximum=0.
  for k,o in validation['outputs'].items():
   a=np.array([.5 if x is None else x for x in o['score']]);b=np.array([.5 if x is None else x for x in vp[ds]['outputs'][k]['score']]);maximum=max(maximum,float(np.max(abs(a-b))))
  meta,x,y,ok,n=population(state,ds,'test');out={k:predict(c,x,ok,n) for k,c in models.items()}
  for k,o in out.items():
   if o['prediction']!=tp[ds]['outputs'][k]['prediction']:raise ValueError('Test decisions differ')
   a=np.array([.5 if x is None else x for x in o['score']]);b=np.array([.5 if x is None else x for x in tp[ds]['outputs'][k]['score']]);maximum=max(maximum,float(np.max(abs(a-b))))
  if maximum>1e-9:raise ValueError('Score reproduction failed')
  rebuilt=summarize(meta,out,selection);original=read(state/'results.json')['datasets'][ds]
  if rebuilt!=original:raise ValueError('Metrics or intervals differ')
  checks[ds]=dict(selected_components=info['parameters']['primary']['names'],max_score_difference=maximum,all_selections_metrics_intervals_equal=True)
 write(state/'reproduction.json',dict(created_utc=now(),checks=checks,no_inference=True))
 print(json.dumps(checks,indent=2))


def export(state,dest):
 state=Path(state);dest=Path(dest);check_freeze(state)
 if dest.exists():raise ValueError('Archive exists')
 dest.mkdir(parents=True)
 for name in ['PLAN.md','AMENDMENTS.md','registration.json','registration-v1.json','registration-v2.json','registration-v3.json','registration-v4.json','freeze.json','models.joblib','fitting.json','selection.json','validation-predictions.json.gz','test-predictions.json.gz','results.json','results.csv','RESULTS.md','reproduction.json','evaluation.json','requirements.txt','jev-refresh-required.json','api-billing.json','billing.json','gpu-billing.json','transport-reconciliation.json','RUN-LOG.md']:
  if (state/name).exists():shutil.copy2(state/name,dest/name)
 for name in ['scores','metadata']:
  shutil.copytree(state/name,dest/name)
 # Public policy versions redact restricted in-context examples. Hashes in the
 # registration identify exact private payloads and earlier frozen provenance.
 for ds,names in POOL.items():
  for model in names:
   policy=read(state/f'policies/{ds}/{model}.json')
   if model=='clef':policy=read(ROOT/DEC/'policies'/model/ds/'final.json')['examples']
   write(dest/f'policies/{ds}/{model}.json',policy)
   if model=='jev':write(dest/f'policies/{ds}/jev-pack-redacted.json',read(ROOT/JEV/'policies'/ds/'final.json'))
 # Canary records contain IDs/hashes/scores only, never content or provider raw responses.
 for p in (state/'new-runs').rglob('*canary*'):
  if p.is_file():
   target=dest/'canary-evidence'/p.relative_to(state/'new-runs');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 f=read(state/'freeze.json')
 for rel in f['sources']:
  target=dest/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
 for rel in ['evals/__init__.py','evals/leaderboard/__init__.py','evals/ensemble/__init__.py']:
  target=dest/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
 (dest/'README.md').write_text('# Cross-family smart ensemble evidence\n\nSee [RESULTS.md](RESULTS.md), [PLAN.md](PLAN.md), and [AMENDMENTS.md](AMENDMENTS.md). The primary system was selected without test feedback; public tests were reused. Jev test scores were refreshed after freezing.\n\n## Reproduce on CPU\n\nFrom this directory, in an environment with `requirements.txt` installed:\n\n```bash\nPYTHONPATH=source python -m evals.smart_ensemble.study reproduce --state .\n```\n\nThis refits classifiers, reselects components and validation cutoffs, and checks all scores, metrics and paired intervals. It makes no API or GPU calls. The bundle contains a checksum-verified project joblib object; only load trusted artifacts. Source prompts and private response bodies are excluded. Published Clef examples and Jev policy packs are redacted; exact private payload hashes and prior freeze provenance are in registration.json. They are not inference-ready replacements for the original data. No downloaded model weights are included.\n')
 write(dest/'checksums.json',dict(sha256={str(p.relative_to(dest)):digest(p) for p in sorted(dest.rglob('*')) if p.is_file()}))
 print('Exported',dest,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['fit','evaluate','reproduce','export']);p.add_argument('--state',required=True);p.add_argument('--dest');a=p.parse_args()
 if a.command=='export':export(a.state,a.dest)
 else:globals()[a.command](a.state)
