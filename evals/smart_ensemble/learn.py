"""Group-cross-validated subset selection, using fitting labels only."""
from itertools import combinations
import numpy as np
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .common import SEED,FAMILY
from evals.leaderboard.metrics import select,decisions,metrics

C_GRID=(.01,.1,1.,10.)
EPS=1e-6
MIN_GAIN=.002
MAX_COMPONENTS=4


def logodds(x):
 x=np.asarray(x,dtype=float)
 if not np.isfinite(x).all() or np.any((x<0)|(x>1)):raise ValueError('Invalid probability features')
 z=np.clip(x,EPS,1-EPS);return np.log(z)-np.log1p(-z)

def logistic(c):
 return make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',max_iter=2000,random_state=SEED))

def as_output(scores,good,native=None):
 p=np.where(good,(scores>=.5).astype(int),-1) if native is None else np.where(good,native,-1)
 return dict(score=[float(s) if ok else None for s,ok in zip(scores,good)],prediction=p.tolist())

def rank(row):
 m=row['choice']['metrics']
 return (-m['balanced_accuracy'],-min(m['recall'],m['specificity']),-m['macro_f1'],row['C'],tuple(row['names']))


class Search:
 def __init__(self,names,x,y,valid,groups):
  self.names=list(names);self.x=logodds(x);self.y=np.asarray(y);self.valid=valid;self.cache={};self.trials=[]
  groups=np.asarray(groups)
  self.folds=list(StratifiedGroupKFold(5,shuffle=True,random_state=SEED).split(x,y,groups))
  for train,held in self.folds:
   if set(groups[train])&set(groups[held]):raise ValueError('Fold group overlap')
  self.fold_ids=np.full(len(y),-1,dtype=int)
  for i,(_,held) in enumerate(self.folds):self.fold_ids[held]=i
  if (self.fold_ids<0).any():raise ValueError('Missing fold assignment')

 def subset(self,names):
  names=tuple(sorted(names))
  if names in self.cache:return self.cache[names]
  cols=[self.names.index(n) for n in names];x=self.x[:,cols];good=self.valid[:,cols].all(1);best=None
  for c in C_GRID:
   oof=np.full(len(self.y),.5)
   for train,held in self.folds:
    fit=train[good[train]]
    if len(np.unique(self.y[fit]))!=2:raise ValueError('One-class training fold')
    clf=logistic(c).fit(x[fit],self.y[fit]);oof[held]=clf.predict_proba(x[held])[:,1]
   output=as_output(oof,good);chosen,_=select(self.y,{'candidate':output})
   row=dict(names=list(names),C=c,choice=chosen['balanced'],excluded_fit_rows=int((~good).sum()))
   self.trials.append(row)
   if best is None or rank(row)<rank(best):best={**row,'oof':output}
  best['model']=logistic(best['C']).fit(x[good],self.y[good]);best['columns']=cols;best['kind']='logistic'
  self.cache[names]=best
  return best

 def forward(self,pool):
  pool=sorted(pool);current=min([self.subset([n]) for n in pool],key=rank)
  path=[dict(step=1,accepted=True,names=current['names'],C=current['C'],oof=current['choice']['metrics'])]
  while len(current['names'])<min(MAX_COMPONENTS,len(pool)):
   options=[self.subset(current['names']+[n]) for n in pool if n not in current['names']]
   if not options:break
   winner=min(options,key=rank)
   gain=winner['choice']['metrics']['balanced_accuracy']-current['choice']['metrics']['balanced_accuracy']
   accepted=gain>=MIN_GAIN-1e-12
   path.append(dict(step=len(current['names'])+1,accepted=accepted,names=winner['names'],C=winner['C'],gain=gain,oof=winner['choice']['metrics'],alternatives=[dict(names=o['names'],C=o['C'],balanced_accuracy=o['choice']['metrics']['balanced_accuracy']) for o in options]))
   if not accepted:break
   current=winner
  return current,path


def predict(c,x,valid,native):
 cols=c['columns'];good=valid[:,cols].all(1);z=x[:,cols];kind=c['kind']
 if kind=='logistic':s=c['model'].predict_proba(logodds(z))[:,1]
 elif kind=='forest':s=c['model'].predict_proba(z)[:,1]
 elif kind=='mean-probability':s=z.mean(1)
 elif kind=='mean-logodds':s=expit(logodds(z).mean(1))
 elif kind=='raw':return as_output(z[:,0],good,native[:,cols[0]])
 else:raise ValueError(kind)
 return as_output(s,good)

def describe(c):
 out={k:c[k] for k in ['kind','names','columns','C','excluded_fit_rows'] if k in c}
 if c['kind']=='logistic':
  scaler,lr=c['model'].steps[0][1],c['model'].steps[1][1]
  a=lr.coef_[0]/scaler.scale_;b=lr.intercept_[0]-np.dot(a,scaler.mean_)
  out.update(standardized_coefficients=dict(zip(c['names'],lr.coef_[0].tolist())),logodds_coefficients=dict(zip(c['names'],a.tolist())),logodds_intercept=float(b),scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),clip=EPS)
 return out

def diagnostics(search,x,y):
 outputs={n:search.subset([n]) for n in search.names}
 preds={n:decisions(r['oof'],r['choice']['threshold']) for n,r in outputs.items()}
 pairs=[]
 for a,b in combinations(search.names,2):
  pa,pb=preds[a],preds[b];wa=pa!=y;wb=pb!=y
  pairs.append(dict(a=a,b=b,both_wrong=int((wa&wb).sum()),a_wrong_b_right=int((wa&~wb).sum()),b_wrong_a_right=int((wb&~wa).sum()),disagree=int((pa!=pb).sum()),a_rescues_b_false_blocks=int(((y==0)&wb&~wa).sum()),a_rescues_b_misses=int(((y==1)&wb&~wa).sum()),b_rescues_a_false_blocks=int(((y==0)&wa&~wb).sum()),b_rescues_a_misses=int(((y==1)&wa&~wb).sum())))
 oracle=np.any(np.stack([p==y for p in preds.values()]),axis=0)
 return dict(note='Fitting OOF diagnostics after bounded tuning; not an unbiased test result',single_oof={n:r['choice'] for n,r in outputs.items()},pairs=pairs,score_correlation=np.corrcoef(x.T).tolist(),feature_order=search.names,oracle_only_diagnostic=dict(accuracy=float(oracle.mean()),remaining_errors=int((~oracle).sum())))

def fit_methods(names,x,y,valid,native,groups):
 search=Search(names,x,y,valid,groups);models={};paths={}
 pools={'primary':names,'open-only':[n for n in names if n!='jev'],'specialist-only':[n for n in names if FAMILY[n]=='specialist'],'decision-only':[n for n in names if FAMILY[n]=='decision']}
 for key,pool in pools.items():models[key],paths[key]=search.forward(pool)
 models['all-logistic']=search.subset(names)
 for n in names:
  models['single/'+n+'/calibrated']=search.subset([n])
  models['single/'+n+'/raw']=dict(kind='raw',names=[n],columns=[names.index(n)])
 for key,pool,kind in [('equal-probability',names,'mean-probability'),('equal-logodds',names,'mean-logodds'),('specialist-equal-logodds',pools['specialist-only'],'mean-logodds')]:
  models[key]=dict(kind=kind,names=list(pool),columns=[names.index(n) for n in pool])
 good=valid.all(1)
 h=HistGradientBoostingClassifier(max_depth=2,max_iter=100,learning_rate=.05,min_samples_leaf=40,l2_regularization=1,class_weight='balanced',early_stopping=False,random_state=SEED).fit(x[good],y[good])
 models['nonlinear']=dict(kind='forest',names=list(names),columns=list(range(len(names))),model=h,excluded_fit_rows=int((~good).sum()))
 for n in models['primary']['names']:
  others=[m for m in models['primary']['names'] if m!=n]
  if others:models['without/'+n]=search.subset(others)
 info=dict(paths=paths,search_trials=search.trials,fold_ids=search.fold_ids.tolist(),fitting_diagnostics=diagnostics(search,x,y),parameters={k:describe(c) for k,c in models.items()},n=len(y),unresolved_by_component=dict(zip(names,(~valid).sum(0).tolist())))
 return models,info
