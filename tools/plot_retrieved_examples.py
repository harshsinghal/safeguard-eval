"""Plot within-model accuracy changes from the frozen retrieval study."""
import argparse
import json
from pathlib import Path

def plot(results, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=json.loads(Path(results).read_text())
    names={'policylm':'PolicyLM 1.7B','shieldstral':'Shieldstral 3B','kev':'Kev 4B','jev':'Jev 1.14'}
    arms=[('fixed_four','Four fixed'),('nearest_four','Four nearest'),('balanced_nearest','Two per class')]
    colors=['#64748b','#1d4ed8','#0f766e']
    fig,axes=plt.subplots(4,1,figsize=(8,8.4),sharex=True)
    plt.rcParams.update({'font.family':'DejaVu Sans'})
    endpoints=[]
    for model in names:
        for arm,_ in arms:
            c=r['paired'][model][arm+' minus policy_only'];endpoints.extend(100*x for x in c['ci95'])
    low=min(-1,min(endpoints)-1);high=max(1,max(endpoints)+1)
    for ax,(model,name) in zip(axes,names.items()):
        ax.axvline(0,color='#94a3b8',lw=1)
        for y,((arm,label),color) in enumerate(zip(arms,colors)):
            c=r['paired'][model][arm+' minus policy_only'];v=100*c['accuracy_difference'];lo,hi=[100*x for x in c['ci95']]
            ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=color,capsize=4,markersize=6)
        ax.set_yticks(range(3),[x[1] for x in arms]);ax.invert_yaxis();ax.set_ylim(2.55,-.55)
        base=r['test'][model]['policy_only']['accuracy']
        ax.set_title(f'{name}  |  Policy-only accuracy: {base:.2%}',loc='left',fontsize=11,pad=10)
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
        ax.grid(axis='x',alpha=.15);ax.set_xlim(low,high)
    axes[-1].set_xlabel('Accuracy change versus the same model without examples (percentage points)')
    fig.suptitle('Do labeled examples help? The effect depends on the model.',x=.03,ha='left',fontsize=15,fontweight='bold',y=.99)
    fig.text(.03,.015,'Same 1,699 WildGuardTest prompts; fixed native decisions, no calibration.\n'
        'Bars: paired 95% bootstrap intervals, unadjusted. Reused benchmark; exploratory study.',fontsize=9,color='#475569')
    fig.tight_layout(rect=(0,.055,1,.96),h_pad=1.9)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--output',required=True)
    plot(**vars(p.parse_args()))
