"""Render the recorded policy-transfer matrix with validation choices marked."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

NAMES={'policylm':'PolicyLM 1.7B','shieldstral':'Shieldstral 3B',
       'qwen-2b':'Qwen3.5 2B','qwen-4b':'Qwen3.5 4B','qwen-27b':'Qwen3.5 27B'}


def plot(analysis, output):
    data=json.loads(Path(analysis).read_text());output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    models=list(NAMES);pool=data['pool']
    labels=[]
    for entry in pool:
        parts=['Initial' if s=='baseline' else 'For '+NAMES[s] for s in entry['sources']]
        labels.append('\n'.join(parts))
    values=np.array([[100*data['matrix']['test'][m][p['id']]['accuracy'] for p in pool] for m in models])
    differences=values-values[:,[0]]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','pdf.fonttype':42})
    fig,axes=plt.subplots(2,1,figsize=(max(9,1.6*len(pool)),8.4),layout='constrained')
    for ax,array,title,limit in [(axes[0],values,'Test accuracy (%)',None),
                                (axes[1],differences,'Change from each recipient’s initial policy (percentage points)',max(1,float(abs(differences).max())))]:
        if limit is None:
            image=ax.imshow(array,cmap='YlGnBu',aspect='auto',vmin=float(values.min())-1,vmax=100)
        else:
            image=ax.imshow(array,cmap='RdBu',aspect='auto',vmin=-limit,vmax=limit)
        for i,m in enumerate(models):
            for j,p in enumerate(pool):
                text=f'{array[i,j]:.2f}' if limit is None else f'{array[i,j]:+.2f}'
                rgba=image.cmap(image.norm(array[i,j]));brightness=.299*rgba[0]+.587*rgba[1]+.114*rgba[2]
                ax.text(j,i,text,ha='center',va='center',color='white' if brightness<.48 else '#15212b',fontsize=11)
                if data['pool_selected'][m]==p['id']:
                    ax.add_patch(Rectangle((j-.48,i-.46),.96,.92,fill=False,edgecolor='#e99c17',linewidth=2.8))
        ax.set(xticks=range(len(pool)),xticklabels=labels,yticks=range(len(models)),yticklabels=[NAMES[m] for m in models])
        ax.set_title(title,loc='left',fontsize=13,pad=14)
        ax.tick_params(axis='both',length=0,pad=9)
        for spine in ax.spines.values():spine.set_visible(False)
        fig.colorbar(image,ax=ax,pad=.02,shrink=.85)
    fig.suptitle('Does a tuned policy travel to another model?',fontsize=18,fontweight='bold',ha='left',x=.02)
    fig.supxlabel('Columns: policies selected using the named source’s validation results.\nGold outline: recipient choice frozen on validation. All cells use the same 1,699 test prompts.\nExploratory study; prior test results were already known. Duplicate policy texts are merged.',fontsize=9)
    for ext in ('png','svg','pdf'):
        fig.savefig(output/('policy-transfer.'+ext),dpi=180,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    with (output/'plotted-data.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['recipient','policy_id','source_attribution','accuracy_percent','change_points','validation_selected'])
        for i,m in enumerate(models):
            for j,p in enumerate(pool):
                writer.writerow([m,p['id'],'|'.join(p['sources']),values[i,j],differences[i,j],data['pool_selected'][m]==p['id']])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();plot(a.analysis,a.out)
