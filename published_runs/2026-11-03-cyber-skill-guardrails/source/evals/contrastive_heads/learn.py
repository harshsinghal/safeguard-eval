"""Identical small heads with and without a supervised contrastive objective."""
import warnings
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from .common import SEEDS,EPOCHS

class Head(nn.Module):
    def __init__(self,width):
        super().__init__()
        self.hidden=nn.Sequential(nn.Linear(width,256),nn.GELU(),nn.Dropout(.1),nn.Linear(256,64),nn.GELU())
        self.output=nn.Linear(64,1)
    def forward(self,x):
        h=self.hidden(x)
        return self.output(h).squeeze(-1),h

def supervised_contrastive(h,y,weights,temperature=.1):
    """Self-exclusion, average positive log probability, weighted valid anchors."""
    z=F.normalize(h,dim=1);sim=z@z.T/temperature
    diagonal=torch.eye(len(y),dtype=torch.bool,device=h.device)
    positives=(y[:,None]==y[None,:]) & ~diagonal
    n=positives.sum(1);valid=n>0
    if not valid.any(): return h.sum()*0
    logden=torch.logsumexp(sim.masked_fill(diagonal,float('-inf')),dim=1)
    logp=sim-logden[:,None]
    losses=-(logp.masked_fill(~positives,0).sum(1)/n.clamp_min(1))
    return (losses[valid]*weights[valid]).sum()/weights[valid].sum()

def standardize(xfit,xval):
    scaler=StandardScaler().fit(xfit)
    # Use the identical arithmetic when reconstructing from saved scaler arrays.
    return scaler,((xfit-scaler.mean_)/scaler.scale_).astype(np.float32),((xval-scaler.mean_)/scaler.scale_).astype(np.float32)

def linear(x,y,xv,c):
    clf=LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',max_iter=3000,tol=1e-6)
    with warnings.catch_warnings(),threadpool_limits(limits=2):
        warnings.simplefilter('error',ConvergenceWarning);clf.fit(x,y)
    return clf,clf.predict_proba(xv)[:,1]

def neural(x,y,xv,decay,seed,contrastive):
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.manual_seed(seed)
    rng=np.random.default_rng(seed)
    net=Head(x.shape[1]);opt=torch.optim.AdamW(net.parameters(),lr=.001,weight_decay=decay)
    xx=torch.from_numpy(x);yy=torch.from_numpy(y.astype(np.float32));vv=torch.from_numpy(xv)
    classweights=len(y)/(2*np.bincount(y,minlength=2));ww=torch.from_numpy(classweights[y].astype(np.float32))
    history=[]
    for epoch in range(1,max(EPOCHS)+1):
        net.train();total=0.;ce_total=0.;scl_total=0.
        for ii in np.array_split(rng.permutation(len(y)),(len(y)+127)//128):
            opt.zero_grad();logits,h=net(xx[ii]);w=ww[ii]
            ce=(F.binary_cross_entropy_with_logits(logits,yy[ii],reduction='none')*w).mean()
            scl=supervised_contrastive(h,yy[ii],w) if contrastive else h.sum()*0
            loss=ce+.1*scl
            if not torch.isfinite(loss): raise ValueError('Nonfinite training loss')
            loss.backward();opt.step();total+=float(loss.detach());ce_total+=float(ce.detach());scl_total+=float(scl.detach())
        history.append(dict(epoch=epoch,loss=total,classification_loss=ce_total,contrastive_loss=scl_total))
        if epoch in EPOCHS:
            net.eval()
            with torch.inference_mode():scores=torch.sigmoid(net(vv)[0]).numpy().astype(float)
            params={k:v.detach().clone() for k,v in net.state_dict().items()}
            yield epoch,params,scores,list(history)

def neural_predict(params,x):
    torch.set_num_threads(4)
    net=Head(x.shape[1]);net.load_state_dict(params);net.eval()
    with torch.inference_mode():return torch.sigmoid(net(torch.from_numpy(x.astype(np.float32)))[0]).numpy().astype(float)
