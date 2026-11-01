"""Plot complete-decision capacity and latency; no accuracy is implied."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(source, destination):
    result=json.loads(source.read_text())
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(12.5,4))
    for engine,color in [('vllm','#2766a8'),('sglang','#c36a21')]:
        data=result['engines'][engine].get('curves',[])
        for ax,concurrency,field,title in zip(axes,[1,32,32],
                ['p50_ms','requests_per_second','p95_ms'],
                ['Single-request median latency','Capacity with 32 requests in flight','p95 latency with 32 requests in flight']):
            values=sorted([r for r in data if r['concurrency']==concurrency and r['content_tokens']!='mixed'],
                          key=lambda r:int(r['content_tokens']))
            if values:
                ax.plot([int(r['content_tokens']) for r in values],[r[field] for r in values],
                        marker='o',label=engine,color=color,lw=2)
            ax.set_xscale('log',base=2)
            ax.set_xticks([64,256,1024,4096],['64','256','1,024','4,096'])
            ax.set_xlabel('Submitted-content tokens')
            ax.set_title(title,fontsize=10)
            ax.grid(alpha=.2)
            ax.set_ylabel('Valid decisions / second' if field=='requests_per_second' else 'Milliseconds')
    axes[0].legend(frameon=False)
    fig.suptitle('Qwen3.5 4B on one NVIDIA L4 · BF16 · prefix caches disabled',fontsize=13)
    fig.text(.5,.015,'Synthetic documents; two 64-request repeats per point. Fixed policy adds input overhead. Not a quality benchmark.',
             ha='center',fontsize=9,color='#475569')
    fig.tight_layout(rect=(0,.055,1,.94))
    destination.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination/'length-curves.png',dpi=180)
    fig.savefig(destination/'length-curves.svg')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();plot(a.source,a.out)
