import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def plot(state,out):
    r=json.loads((Path(state)/'results.json').read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),sharey=True)
    keys=['policylm/lr','policylm/mlp','policylm/contrastive','modernbert/lr','modernbert/mlp','modernbert/contrastive']
    names=['PolicyLM · linear','PolicyLM · neural','PolicyLM · contrastive','ModernBERT · linear','ModernBERT · neural','ModernBERT · contrastive']
    for ax,ds,title in zip(axes,['wildguard','hatexplain'],['WildGuard · 1,699 prompts','HateXplain · 1,924 posts']):
        rr=r['results'][ds];yy=np.arange(len(keys))[::-1]
        for j,key in enumerate(keys):
            m=rr['profiles']['balanced'][key]['seed_metrics'][0];lo,hi=rr['ci95'][key]['balanced_accuracy'];ba=m['balanced_accuracy']
            ax.errorbar(100*ba,yy[j]+.1,xerr=np.array([[100*(ba-lo)],[100*(hi-ba)]]),fmt='o',color='#246a98',capsize=3,label='Balanced accuracy + 95% interval' if j==0 else None)
            ax.scatter(100*m['accuracy'],yy[j]-.13,marker='s',s=26,color='#a05b18',label='Ordinary accuracy' if j==0 else None)
        ax.set_title(title,fontsize=12,loc='left',pad=14);ax.set_xlabel('Test accuracy (%)')
        ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.spines[['top','right','left']].set_visible(False)
        ax.axhline(2.5,color='#cbd5e1',lw=.8);ax.set_ylim(-.7,5.7)
        ax.set_xlim(50,100)
    axes[0].set_yticks(np.arange(6)[::-1],names,fontsize=10)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.54,.02),fontsize=9)
    fig.suptitle('Does contrastive training improve a small moderation classifier?',x=.04,ha='left',fontsize=15,y=.98)
    fig.text(.04,.005,'Validation-selected balanced settings; fixed primary seed. Reused public tests; exploratory intervals.',fontsize=8,color='#475569')
    fig.tight_layout(rect=[0,.10,1,.92]);fig.savefig(out/'accuracy-comparison.png',dpi=180);fig.savefig(out/'accuracy-comparison.svg')
    p=out/'accuracy-comparison.svg';p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True);plot(**vars(p.parse_args()))
