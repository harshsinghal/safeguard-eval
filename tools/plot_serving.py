"""Render the measured latency/throughput curves, without extrapolation."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS={'liquid':'Liquid encoder 350M, fine-tuned','policylm':'PolicyLM 1.7B',
        'shieldstral':'Shieldstral 3B','qwen-4b':'Qwen3.5 4B','wildguard':'WildGuard 7B',
        'kev':'Kev 4B','clef':'Clef-Flash 9B'}


def plot(summary,output,optimized=None,cached=False):
    data=json.loads(Path(summary).read_text());output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if optimized:
        faster=json.loads(Path(optimized).read_text())
        slugs={r['model'] for r in faster}
        data=[r for r in data if r['model'] not in slugs]+faster
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11.5,5.5))
    colors=plt.get_cmap('tab10').colors
    for index,slug in enumerate(LABELS):
        rr=sorted((r for r in data if r['model']==slug and r['cache']==(cached and r['backend']=='vllm')),key=lambda r:r['concurrency'])
        if not rr:continue
        style='-' if rr[0]['backend']=='vllm' else '--'
        x=[r['concurrency'] for r in rr]
        axes[0].plot(x,[r['requests_per_second'] for r in rr],marker='o',linestyle=style,color=colors[index],label=LABELS[slug])
        axes[1].plot(x,[r['p95_ms'] for r in rr],marker='o',linestyle=style,color=colors[index])
    for ax in axes:
        ax.set_xscale('log',base=2);ax.set_xticks([1,8,32,64],[1,8,32,64]);ax.set_xlabel('Concurrent requests');ax.grid(alpha=.18)
    axes[0].set_ylabel('Valid classifications / second');axes[0].set_yscale('log');axes[0].set_title('How much work gets done')
    axes[1].set_ylabel('95th-percentile request latency (ms)');axes[1].set_yscale('log');axes[1].set_title('How long a request waits')
    fig.suptitle('More concurrent requests trade latency for throughput',fontsize=16,x=.08,ha='left')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,-.025))
    cache_label='on' if cached else 'off'
    kernel_label=' · optimized decision kernels' if optimized else ''
    fig.text(.08,.865,f'One L40S · 384 unique prompts × 3 repeats · vLLM prefix cache {cache_label}{kernel_label}\nSolid: vLLM 0.32.0. Dashed: native PyTorch batch server. Both vertical scales are logarithmic.',fontsize=9,color='#475569')
    fig.subplots_adjust(top=.77,bottom=.23,wspace=.28)
    for ext in ('png','svg'):fig.savefig(output/('concurrency.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--summary',required=True);p.add_argument('--output',required=True)
    p.add_argument('--optimized');p.add_argument('--cached',action='store_true')
    a=p.parse_args();plot(**vars(a))
