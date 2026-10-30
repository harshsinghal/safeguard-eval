"""Show the full policy/cutoff comparison for both interpreters and populations."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(state,out):
    r=json.loads((Path(state)/'results.json').read_text())
    names=['baseline-native','baseline-tuned','revised-native','revised-tuned']
    labels=['Original policy · cutoff 0.5','Original policy · tuned cutoff',
            'Revised policy · cutoff 0.5','Revised policy · tuned cutoff']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(13,5.5),layout='constrained',sharey=True)
    colors={'shieldstral':'#235D70','qwen':'#B2673B'}
    for ax,split,title in zip(axes,['holdout','test'],['Additional project holdout (2,048)','Reused WildGuardTest (1,699)']):
        d=r['datasets'][split];values=[]
        for model,offset in [('shieldstral',-.13),('qwen',.13)]:
            for j,name in enumerate(names):
                m=d['primary'][model][name]['metrics'];v=100*m['balanced_accuracy']
                lo,hi=np.array(d['ci95'][model+'/'+name]['balanced_accuracy'])*100;values.extend([lo,hi])
                ax.errorbar(v,j+offset,xerr=[[v-lo],[hi-v]],fmt='o',color=colors[model],markersize=7,capsize=3,
                    label=('Shieldstral 3B' if model=='shieldstral' else 'Qwen 4B') if j==0 else None)
                ax.text(hi+.22,j+offset,f'{v:.2f}%',va='center',fontsize=9,color=colors[model])
        ax.set_yticks(range(4),labels);ax.set_ylim(3.6,-.65)
        ax.set_xlim(max(0,np.floor(min(values))-1),min(102,np.ceil(max(values))+2))
        ax.set_xlabel('Balanced accuracy (%)');ax.set_title(title,loc='left',fontweight='bold')
        ax.grid(axis='x',color='#e4e7ec');ax.legend(loc='lower left',frameon=False,fontsize=9)
    fig.suptitle('One policy correction, two interpreters',fontweight='bold',fontsize=17)
    fig.supxlabel('Policies and cutoffs chosen before final inference · Fixed model weights · 95% paired group-bootstrap intervals',fontsize=10)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg']:fig.savefig(out/('policy-and-cutoff.'+ext),dpi=180)
    p=out/'policy-and-cutoff.svg';p.write_text('\n'.join(x.rstrip() for x in p.read_text().splitlines())+'\n')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();plot(a.state,a.out)
