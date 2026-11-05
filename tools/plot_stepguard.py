"""Plot already-scored StepGuard results; never selects a policy or threshold."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main(results,output):
    source=json.loads(Path(results).read_text())['results']
    models=['shieldstral','safeguard','jev','kev','clef']
    names=['Shieldstral 3B','GPT-OSS Safeguard 20B','Jev 1.14 (API)','Kev 4B','Clef Flash 9B']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False})
    fig,axes=plt.subplots(1,2,figsize=(13,5.2),sharey=True,layout='constrained')
    for ax,task,title in zip(axes,('action','trajectory'),('Pending action','Completed run')):
        panel=source[task]['primary'];yy=np.arange(len(models))
        for arm,offset,color,label in (('initial',-.18,'#bac4cc','Initial policy'),('selected',.18,'#177f8d','Validation-selected policy')):
            x=[100*panel['models'][m][arm]['metrics']['balanced_accuracy'] for m in models]
            ax.barh(yy+offset,x,height=.32,color=color,label=label,zorder=3)
            if arm=='selected':
                intervals=np.array([panel['models'][m][arm]['intervals95']['balanced_accuracy'] for m in models])*100
                ax.errorbar(x,yy+offset,xerr=np.stack((np.array(x)-intervals[:,0],intervals[:,1]-np.array(x))),
                    fmt='none',ecolor='#20333b',elinewidth=1,capsize=2,zorder=4)
                for y,v in zip(yy+offset,x):ax.text(min(v+4.5,99),y,f'{v:.1f}',va='center',fontsize=9)
        ax.set_yticks(yy,names);ax.invert_yaxis();ax.set_xlim(0,105)
        ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('Balanced accuracy (%)')
        ax.set_title(f'{title} · {panel["n"]:,} held-out records',loc='left',fontweight='bold',pad=13)
        ax.grid(axis='x',color='#e6eaed',zorder=0);ax.tick_params(axis='y',length=0)
    # Shared y-axis needs only one inversion.
    axes[0].set_ylim(len(models)-.5,-.5)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
    fig.suptitle('Policy selection can change agent-behavior classification',fontsize=15,fontweight='bold',x=.02,ha='left')
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,dpi=180,facecolor='white');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--output',required=True)
    main(**vars(p.parse_args()))
