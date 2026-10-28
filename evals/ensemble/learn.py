"""Small, bounded ensemble search, with all transformations fitted on training only."""
import numpy as np
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evals.ensemble.common import SEED,metrics

C_GRID=[.01,.1,1.,10.,100.]
THRESHOLDS=np.r_[np.arange(101)/100,1.000000001]


def logistic(C):
    return make_pipeline(StandardScaler(),LogisticRegression(C=C,max_iter=2000,random_state=SEED))


def calibrators(X,y,groups):
    """OOF values fit learned soft voting; full-training transforms serve held-outs."""
    splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=SEED)
    oof=np.zeros_like(X);covered=np.zeros(len(y),dtype=int)
    for train,test in splitter.split(X,y,groups):
        if set(np.asarray(groups)[train]) & set(np.asarray(groups)[test]):raise ValueError('Calibration fold leaks groups')
        for j in range(X.shape[1]):
            model=logistic(1.).fit(X[train,j:j+1],y[train])
            oof[test,j]=model.predict_proba(X[test,j:j+1])[:,1]
        covered[test]+=1
    if not np.all(covered==1):raise ValueError('Invalid OOF coverage')
    full=[logistic(1.).fit(X[:,j:j+1],y) for j in range(X.shape[1])]
    return oof,full


def calibrated(X,models):
    return np.column_stack([m.predict_proba(X[:,j:j+1])[:,1] for j,m in enumerate(models)])


def weighted_fit(X,y,strength):
    k=X.shape[1]
    def loss(w):
        p=np.clip(X@w,1e-7,1-1e-7)
        return -np.mean(y*np.log(p)+(1-y)*np.log(1-p))+strength*np.sum((w-1/k)**2)
    result=minimize(loss,np.full(k,1/k),method='SLSQP',bounds=[(0.,1.)]*k,
        constraints=[{'type':'eq','fun':lambda w:np.sum(w)-1}],options={'maxiter':1000,'ftol':1e-12})
    if not result.success or abs(result.x.sum()-1)>1e-6 or np.any(result.x < -1e-8):
        raise RuntimeError('Simplex fit failed: '+result.message)
    return result.x,dict(training_objective=float(result.fun),iterations=int(result.nit))


def predict(candidate,X):
    kind=candidate['kind']
    if kind=='single-raw':return X[:,candidate['column']]
    if kind=='single-logistic':return candidate['model'].predict_proba(X[:,candidate['column']:candidate['column']+1])[:,1]
    if kind=='equal-raw':return X.mean(axis=1)
    if kind=='equal-calibrated':return calibrated(X,candidate['calibrators']).mean(axis=1)
    if kind=='weighted':return calibrated(X,candidate['calibrators'])@candidate['weights']
    if kind in ('logistic','forest'):return candidate['model'].predict_proba(X)[:,1]
    raise ValueError('Unknown candidate')


def classify(score,valid,threshold):
    return np.where(valid,(score>=threshold).astype(int),-1)


def validity(candidate,mask):
    """An individual is not penalized for a different model's failed response."""
    if mask.ndim==1:return mask
    return mask[:,candidate['column']] if candidate['kind'].startswith('single-') else mask.all(axis=1)


def threshold(meta,score,valid,fixed=None):
    values=[]
    for t in [fixed] if fixed is not None else THRESHOLDS:
        m=metrics(meta,classify(score,valid,t))
        values.append(dict(threshold=float(t),accuracy=m['accuracy'],macro_f1=m['macro_f1']))
    return max(values,key=lambda r:(r['accuracy'],r['macro_f1'],-abs(r['threshold']-.5),-r['threshold']))


def search(names,train_meta,X,y,train_valid,val_meta,V,val_valid):
    # Missing base predictions never become valid artificial features for fitting.
    complete=train_valid.all(axis=1) if train_valid.ndim==2 else train_valid
    groups=np.array([r['group'] for r in train_meta])[complete]
    Xt,yt=X[complete],y[complete]
    if len(np.unique(yt))!=2:raise ValueError('Both training classes required')
    oof,full=calibrators(Xt,yt,groups)
    candidates=[]
    for j,name in enumerate(names):
        for mode in ['fixed','thresholded']:
            candidates.append(dict(id=f'single/{name}/{mode}',family='single',kind='single-raw',column=j,
                fixed_threshold=.5 if mode=='fixed' else None))
        for C in C_GRID:
            own_valid=train_valid[:,j] if train_valid.ndim==2 else train_valid
            candidates.append(dict(id=f'single/{name}/logistic-C{C:g}',family='single',kind='single-logistic',column=j,
                model=logistic(C).fit(X[own_valid,j:j+1],y[own_valid]),C=C))
    candidates.append(dict(id='equal/raw',family='equal-raw',kind='equal-raw'))
    candidates.append(dict(id='equal/calibrated',family='equal-calibrated',kind='equal-calibrated',calibrators=full))
    for strength in [0.,.01,.1]:
        weights,info=weighted_fit(oof,yt,strength)
        candidates.append(dict(id=f'weighted/lambda{strength:g}',family='weighted',kind='weighted',weights=weights,
            strength=strength,calibrators=full,optimization=info))
    for C in C_GRID:
        candidates.append(dict(id=f'logistic/C{C:g}',family='logistic',kind='logistic',C=C,model=logistic(C).fit(Xt,yt)))
    for depth in [2,4]:
        for leaf in [20,80]:
            m=RandomForestClassifier(n_estimators=300,max_depth=depth,min_samples_leaf=leaf,random_state=SEED,n_jobs=2).fit(Xt,yt)
            candidates.append(dict(id=f'forest/depth{depth}-leaf{leaf}',family='forest',kind='forest',model=m,depth=depth,leaf=leaf))
    records=[]
    for c in candidates:
        score=predict(c,V); valid=validity(c,val_valid); chosen=threshold(val_meta,score,valid,c.get('fixed_threshold'))
        c['threshold']=chosen['threshold']
        record=dict(id=c['id'],family=c['family'],kind=c['kind'],selected_threshold=c['threshold'],
                    validation=metrics(val_meta,classify(score,valid,c['threshold']),score),parameters={k:c[k] for k in ('C','strength','depth','leaf','column') if k in c})
        if 'weights' in c:record['weights']=c['weights'].tolist()
        if c['kind'] in ('logistic','single-logistic'):
            model=c['model'];lr=model.steps[-1][1];sc=model.steps[0][1]
            record['logistic_parameters']=dict(coefficients=lr.coef_[0].tolist(),intercept=float(lr.intercept_[0]),
                feature_means=sc.mean_.tolist(),feature_scales=sc.scale_.tolist())
        records.append(record)
    def rank(r):
        return (-r['validation']['accuracy'],-r['validation']['macro_f1'],abs(r['selected_threshold']-.5),r['selected_threshold'],r['id'])
    selected={family:min([r for r in records if r['family']==family],key=rank)['id'] for family in sorted({r['family'] for r in records})}
    best_ensemble=min([r for r in records if r['family']!='single'],key=rank)['id']
    return candidates,dict(candidates=records,selected=selected,best_ensemble=best_ensemble,primary=selected['logistic'],
        best_single=selected['single'],fitting_rows=int(complete.sum()),excluded_training_failures=int((~complete).sum()),
        feature_names=names,calibration_folds=5,selection='validation accuracy, macro-F1, threshold nearest .5, lower threshold, lexical ID')
