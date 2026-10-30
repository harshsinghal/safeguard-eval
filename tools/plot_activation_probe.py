"""Plot registered primary comparisons, without ranking by test results."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(state,out):
    result=json.loads((Path(state)/'test-results.json').read_text())
    names=['policylm-native','primary-qwen','primary-policylm','primary-combined']
    labels=['PolicyLM native score','Qwen 0.8B features + LR','PolicyLM 1.7B features + LR','Combined features + LR']
    rr=[result['profiles']['balanced'][n]['test'] for n in names]
    ba=np.array([r['balanced_accuracy']*100 for r in rr])
    ci=np.array([result['ci95'][n]['balanced_accuracy'] for n in names])*100
    colors=['#7C879A','#5683A9','#527D68','#263D6A'];yy=np.arange(len(names))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(12.5,4.8),gridspec_kw={'width_ratios':[1.25,1]},layout='constrained')
    for i,c in enumerate(colors):
        ax.errorbar(ba[i],i,xerr=[[ba[i]-ci[i,0]],[ci[i,1]-ba[i]]],fmt='o',color=c,markersize=9,capsize=4)
        ax.text(ci[i,1]+.25,i,f'{ba[i]:.2f}%',va='center',fontsize=10,color=c)
    ax.set_yticks(yy,labels);ax.set_ylim(3.9,-.4);ax.set_xlabel('Balanced accuracy (%)')
    ax.set_xlim(max(0,np.floor(ci.min())-2),min(100,np.ceil(ci.max())+5))
    ax.grid(axis='x',color='#e4e7ec');ax.set_title('Primary comparisons',loc='left',fontweight='bold')
    fp=np.array([r['false_positive_rate']*100 for r in rr]);fn=np.array([r['false_negative_rate']*100 for r in rr])
    bx.barh(yy-.16,fp,height=.29,color='#8C6075',label='Benign prompts falsely blocked')
    bx.barh(yy+.16,fn,height=.29,color='#66849A',label='Harmful prompts missed')
    for values,offset in [(fp,-.16),(fn,.16)]:
        for i,v in enumerate(values):bx.text(v+.3,i+offset,f'{v:.1f}%',va='center',fontsize=9)
    bx.set_yticks(yy,[]);bx.set_ylim(3.9,-.4);bx.set_xlabel('Error rate within the relevant class (%)')
    bx.set_xlim(0,max(fp.max(),fn.max())+5);bx.grid(axis='x',alpha=.2)
    bx.set_title('The two kinds of errors',loc='left',fontweight='bold');bx.legend(loc='lower left',fontsize=8,frameon=False)
    fig.suptitle('Frozen representations for WildGuard prompt classification',fontsize=15,fontweight='bold')
    fig.supxlabel('4,096 fitting · 1,536 validation · 1,699 test prompts | Cutoffs chosen on validation | 95% group-bootstrap intervals',fontsize=9)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg']:fig.savefig(out/('primary-comparisons.'+ext),dpi=180)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    args=p.parse_args();plot(args.state,args.out)
