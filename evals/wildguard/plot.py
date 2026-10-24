"""Standalone publication figures from frozen test analysis (requires matplotlib)."""
import argparse
import csv
import json
from pathlib import Path


def plot(analysis,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a=json.loads(Path(analysis).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    labels={'shieldstral':'Shieldstral-3B (primary)','cope':'CoPE-B-A4B','safeguard':'GPT-OSS Safeguard-20B','policylm':'PolicyLM-1.7B'}
    baseline=next(e for e in a['entries'] if e['adapter']=='wildguard')
    records=[]
    for model,label in labels.items():
        initial=next(e for e in a['entries'] if e['adapter']==model and 'initial' in e['roles'])
        tuned=next(e for e in a['entries'] if e['adapter']==model and 'individual' in e['roles'])
        d=tuned['vs_initial']
        records.append(dict(model=model,label=label,initial=100*initial['metrics']['accuracy'],
            tuned=100*tuned['metrics']['accuracy'],delta=100*d['delta'],lower=100*d['ci95'][0],upper=100*d['ci95'][1]))
    with (out/'policy-tuning.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(12,5.6),gridspec_kw={'width_ratios':[1.15,1]})
    fig.subplots_adjust(left=.205,right=.97,top=.76,bottom=.24,wspace=.3)
    gray='#6b7280';blue='#1764a0';red='#a23d4a'
    for i,r in enumerate(records):
        axes[0].plot([r['initial'],r['tuned']],[i,i],color='#c4cbd4',lw=2,zorder=1)
        axes[0].scatter(r['initial'],i,color=gray,s=40,label='Initial policy' if i==0 else None,zorder=3)
        axes[0].scatter(r['tuned'],i,color=blue,s=50,label='Validation-selected policy' if i==0 else None,zorder=3)
        axes[0].annotate(f"{r['initial']:.2f}",(r['initial'],i),xytext=(0,-15),textcoords='offset points',ha='center',color=gray,fontsize=9)
        axes[0].annotate(f"{r['tuned']:.2f}",(r['tuned'],i),xytext=(0,8),textcoords='offset points',ha='center',color=blue,fontsize=9)
        axes[1].errorbar(r['delta'],i,xerr=[[r['delta']-r['lower']],[r['upper']-r['delta']]],fmt='o',color=blue,capsize=4,lw=1.7)
        axes[1].annotate(f"{r['delta']:+.2f}  [{r['lower']:+.2f}, {r['upper']:+.2f}]",(r['delta'],i),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
    wg=100*baseline['metrics']['accuracy']
    axes[0].axvline(wg,color=red,ls='--',lw=1.2,label=f'WildGuard: {wg:.2f}%')
    axes[0].set_yticks(range(len(records)),[r['label'] for r in records])
    axes[1].set_yticks(range(len(records)),['']*len(records))
    axes[0].set_xlabel('Test accuracy (%)')
    axes[1].set_xlabel('Gain over initial policy (percentage points)')
    axes[1].axvline(0,color=gray,lw=1,ls='--')
    axes[0].set_xlim(min(r['initial'] for r in records)-1.8,max(max(r['tuned'] for r in records),wg)+1.5)
    axes[1].set_xlim(min(0,min(r['lower'] for r in records))-.8,max(r['upper'] for r in records)+.8)
    for ax in axes:
        ax.set_ylim(len(records)-.55,-.65);ax.grid(axis='x',alpha=.16)
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    handles,names=axes[0].get_legend_handles_labels()
    fig.legend(handles,names,loc='upper left',bbox_to_anchor=(.198,.885),frameon=False,ncol=3,fontsize=9)
    fig.text(.025,.97,'Frozen policy tuning on WildGuardTest',fontsize=18,weight='bold',va='top')
    fig.text(.025,.915,'1,699 labeled prompts · fixed model weights · fixed primary thresholds · failures count as incorrect',fontsize=10,color='#374151')
    primary=next(e for e in a['entries'] if e['adapter']==a['primary']['adapter'] and e['policy_id']==a['primary']['policy_id'])
    d=primary['vs_wildguard'];lo,hi=[100*x for x in d['ci95']]
    fig.text(.025,.11,f"Primary comparison vs WildGuard: {100*d['delta']:+.2f} points (95% CI {lo:+.2f} to {hi:+.2f}).",fontsize=11,weight='bold')
    fig.text(.025,.065,'Intervals use 2,000 paired group-bootstrap replicates. Model-specific policy comparisons are exploratory; no multiple-comparison correction.',fontsize=8.5,color='#4b5563')
    fig.text(.025,.03,'One benchmark and one search run; training exposure is not fully known. See methods and separate threshold-calibration controls.',fontsize=8.5,color='#4b5563')
    fig.savefig(out/'policy-tuning.png',dpi=180,facecolor='white')
    fig.savefig(out/'policy-tuning.svg',facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();plot(a.analysis,a.out)
