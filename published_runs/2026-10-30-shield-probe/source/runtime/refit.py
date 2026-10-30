from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path.cwd()))
from evals.shield_probe import study
from evals.shield_probe.common import read,write,now,labels,matrix
root=Path('../work/shield-probe-run/state')
study.check_freeze(root,include_features=True)
fm,xf,vf,_=study.all_features(root,'fit');vm,xv,vv,_=study.all_features(root,'validation')
y=labels(fm);specs=read(root/'fits.json');saved=read(root/'validation.json')['candidates'];diffs=[]
for cid,spec in specs.items():
 reps=spec['representation'];fitok=study.validity_for(vf,reps);valok=study.validity_for(vv,reps)
 params,_=study.fit_linear(matrix(xf,reps)[fitok],y[fitok],spec['C'])
 with np.load(root/spec['path'],allow_pickle=False) as old:
  for key in params:
   if not np.array_equal(params[key],old[key]):raise ValueError('Parameter mismatch '+cid+'/'+key)
 score=study.predict(params,matrix(xv,reps)[valok]);old=np.asarray(saved[cid]['score'],dtype=float)[valok]
 delta=float(np.max(np.abs(score-old)));diffs.append(delta)
 if delta>1e-9:raise ValueError('Validation mismatch '+cid)
 print(cid,'max_difference',delta,flush=True)
write(root/'refit-reproduction.json',dict(verified_utc=now(),candidate_fits=len(specs),parameter_arrays_exact=True,maximum_validation_score_difference=max(diffs),validation_score_tolerance=1e-9))
print('ALL_REFITS_REPRODUCED',len(specs),flush=True)
