"""A bounded representation ablation; no language-model inference or tuning."""
import numpy as np
from scipy.special import expit

from evals.ensemble.common import metrics
from evals.ensemble.learn import C_GRID, logistic, threshold, classify, validity, predict as prior_predict


def log_odds(scores):
    x=np.asarray(scores,dtype=np.float64)
    if not np.isfinite(x).all() or np.any(x<=0) or np.any(x>=1):
        raise ValueError('Log-odds require finite scores strictly between zero and one')
    return np.log(x)-np.log1p(-x)


def predict(candidate,scores):
    kind=candidate['kind']
    if kind=='single-logit':
        j=candidate['column']
        return candidate['model'].predict_proba(log_odds(scores[:,j:j+1]))[:,1]
    if kind=='logit-logistic':
        return candidate['model'].predict_proba(log_odds(scores))[:,1]
    if kind=='logit-equal':return expit(log_odds(scores).mean(axis=1))
    return prior_predict(candidate,scores)


def rank(record):
    m=record['validation'];t=record['selected_threshold']
    return (-m['accuracy'],-m['macro_f1'],abs(t-.5),t,record['id'])


def search(names,X,y,train_valid,val_meta,V,val_valid,prior_selection):
    complete=train_valid.all(axis=1)
    if len(np.unique(y[complete]))!=2:raise ValueError('Both training classes required')
    # Failed rows have a placeholder only for shape; they are excluded from fitting.
    Z=log_odds(X);new=[]
    for j,name in enumerate(names):
        own=train_valid[:,j]
        for C in C_GRID:
            model=logistic(C).fit(Z[own,j:j+1],y[own])
            new.append(dict(id=f'logit-single/{name}/C{C:g}',family='single',kind='single-logit',column=j,C=C,model=model))
    for C in C_GRID:
        model=logistic(C).fit(Z[complete],y[complete])
        new.append(dict(id=f'logit-logistic/C{C:g}',family='logit-logistic',kind='logit-logistic',C=C,model=model))
    new.append(dict(id='logit-equal',family='logit-equal',kind='logit-equal'))
    records=[]
    for c in new:
        s=predict(c,V);valid=validity(c,val_valid)
        c['threshold']=threshold(val_meta,s,valid)['threshold']
        r=dict(id=c['id'],family=c['family'],kind=c['kind'],selected_threshold=c['threshold'],
            parameters={k:c[k] for k in ['C','column'] if k in c},validation=metrics(val_meta,classify(s,valid,c['threshold']),s))
        if 'model' in c:
            scaler,model=c['model'].steps[0][1],c['model'].steps[-1][1]
            r['logistic_parameters']=dict(coefficients=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),
                feature_means=scaler.mean_.tolist(),feature_scales=scaler.scale_.tolist())
        records.append(r)
    singles=[r for r in records if r['family']=='single']+[r for r in prior_selection['candidates'] if r['family']=='single']
    primary=min([r for r in records if r['family']=='logit-logistic'],key=rank)['id']
    per_model={name:min([r for r in singles if r['id'].startswith((f'single/{name}/',f'logit-single/{name}/'))],key=rank)['id'] for name in names}
    selected=dict(primary=primary,secondary='logit-equal',best_single=min(singles,key=rank)['id'],
        per_model=per_model,prior_probability_logistic=prior_selection['primary'],prior_best_single=prior_selection['best_single'],
        prior_best_ensemble=prior_selection['best_ensemble'])
    return new,dict(created_from='fitting and validation only',candidates=records,single_pool=singles,selected=selected,
        feature_names=names,fitting_rows=int(complete.sum()),excluded_training_failures=int((~complete).sum()),
        selection='validation accuracy, macro-F1, threshold nearest .5, lower threshold, lexical ID')
