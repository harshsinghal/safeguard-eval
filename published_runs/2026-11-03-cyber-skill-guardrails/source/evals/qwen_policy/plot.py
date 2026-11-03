"""Render an exportable, paired accuracy comparison from recorded analysis."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(analysis,out):
    data=json.loads(Path(analysis).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=False)
    rows=[p for p in data['paired_comparisons'] if p['role']=='selected']
    names={'policylm':'PolicyLM 1.7B','shieldstral':'Shieldstral 3B','wildguard':'WildGuard 7B','cope':'CoPE 25.2B / 3.8B active','safeguard':'Safeguard 20B / 3.6B active'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig,(left,right)=plt.subplots(1,2,figsize=(13,6.7),gridspec_kw={'width_ratios':[1.15,1]},sharey=True)
    labels=[];export=[]
    for i,p in enumerate(rows):
        q=p['model'].split('Qwen3.5-')[1];label='Qwen '+q+' vs '+names[p['comparator']];labels.append(label)
        qa=100*p['qwen_metrics']['accuracy'];pa=100*p['policy_model_metrics']['accuracy'];d=p['qwen_minus_policy'];v=100*d['delta'];lo,hi=[100*x for x in d['ci95']]
        left.plot([pa,qa],[i,i],color='#b9c4cd',lw=2,zorder=1)
        left.scatter(pa,i,color='#a85d14',s=52,label='Specialist' if i==0 else None,zorder=3)
        left.scatter(qa,i,color='#176da2',s=52,label='Qwen' if i==0 else None,zorder=3)
        right.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',color='#176da2',capsize=4)
        right.annotate(f'{v:+.2f}',(hi,i),xytext=(7,0),textcoords='offset points',va='center',fontsize=9)
        export.append(dict(pair=label,qwen_accuracy=qa,specialist_accuracy=pa,delta_percentage_points=v,ci95_low=lo,ci95_high=hi))
    left.set_yticks(range(len(rows)),labels);left.invert_yaxis();left.set_xlabel('Test accuracy (%)');right.set_xlabel('Qwen minus specialist (percentage points)')
    left.set_title('Validation-selected prompts',loc='left',fontweight='bold');right.set_title('Paired 95% intervals',loc='left',fontweight='bold');right.axvline(0,color='#777',lw=1,ls='--')
    left.legend(loc='lower left',frameon=False);left.grid(axis='x',alpha=.2);right.grid(axis='x',alpha=.2);right.margins(x=.28)
    fig.suptitle('General-purpose Qwen and nearby-size policy models',x=.03,ha='left',fontsize=16,fontweight='bold')
    fig.text(.03,.035,'WildGuardTest: all 1,699 labeled prompts. Exploratory, unadjusted group-bootstrap intervals.\nApproximate size matches; architectures and deployments differ. Large Qwen runs are reused across two comparisons.',fontsize=9,color='#4b5563')
    fig.subplots_adjust(left=.30,right=.98,top=.86,bottom=.17,wspace=.15)
    for suffix in ['png','svg']:fig.savefig(out/('qwen-comparison.'+suffix),dpi=220,facecolor='white')
    svg=out/'qwen-comparison.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().split('\n')).rstrip()+'\n')
    plt.close(fig)
    with (out/'qwen-comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(export[0]),lineterminator='\n');w.writeheader();w.writerows(export)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True);p.add_argument('--out',required=True);a=p.parse_args();plot(a.analysis,a.out)
