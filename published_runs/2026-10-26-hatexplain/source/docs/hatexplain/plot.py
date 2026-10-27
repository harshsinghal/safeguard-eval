"""Readable supporting figures; all plotted values come from the recorded analysis."""
import argparse
import json
from pathlib import Path


def plot(analysis, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    data = json.loads(Path(analysis).read_text()); out = Path(out); out.mkdir(parents=True, exist_ok=True)
    names = {'policylm': 'PolicyLM 1.7B', 'shieldstral': 'Shieldstral 3B', 'qwen-4b': 'Qwen3.5-4B'}
    models = list(names)
    lookup = {(c['model'], c['policy_id'], c['variant']): c for c in data['conditions'] if not c['repeat']}
    sources = ['Shared policy\n(PolicyLM retained this)', 'Context clarification\n(selected for Shieldstral)',
               'Punctuation revision\n(selected for Qwen)']
    columns = ['p0', data['selections']['shieldstral'], data['selections']['qwen-4b']]
    values = np.array([[100*lookup[(m, p, 'markdown')]['macro_f1'] for p in columns] for m in models])
    base = values[:, :1]; delta = values-base
    fig, ax = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    bound = max(1., float(np.max(np.abs(delta))))
    im = ax.imshow(delta, cmap='RdBu', vmin=-bound, vmax=bound, aspect='auto')
    ax.set_xticks(range(len(columns)), sources, fontsize=9); ax.set_yticks(range(3), [names[m] for m in models])
    for i in range(3):
        for j in range(len(columns)):
            ax.text(j, i, f'{values[i,j]:.1f}\n({delta[i,j]:+.1f} pp)', ha='center', va='center',
                    color='white' if abs(delta[i,j]) > .65*bound else '#19222c', fontsize=11)
    ax.set_title('Small wording revisions had small, mixed effects', loc='left', fontsize=15, pad=18)
    ax.set_xlabel('Policy source · numbers show binary macro-F1 (%) and change from the shared policy', labelpad=14)
    ax.set_ylabel('Model applying the policy')
    fig.colorbar(im, ax=ax, label='Change in macro-F1 (percentage points)', shrink=.8)
    fig.savefig(out/'policy-transfer.png', dpi=180); fig.savefig(out/'policy-transfer.svg'); plt.close(fig)
    variants = ['omit-definitions', 'omit-exceptions', 'omit-allow-examples', 'omit-all-examples']
    labels = ['Definitions removed', 'Exception section removed', 'ALLOW examples removed', 'All examples removed']
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, m in zip(axes, models):
        for i, v in enumerate(variants):
            entry = next(c for c in data['contrasts'] if c['model']==m and c['policy_id']=='p0' and c['variant']==v)
            value=entry['macro_f1_delta']*100; low,high=[x*100 for x in entry['macro_f1_ci95']]
            ax.errorbar(value, i, xerr=[[max(0,value-low)],[max(0,high-value)]], fmt='o', color='#1f5c85', capsize=3)
        ax.axvline(0, color='#9ba4ae', lw=1); ax.set_title(names[m]); ax.set_xlabel('Macro-F1 change (pp)'); ax.grid(axis='x', alpha=.15)
    axes[0].set_yticks(range(4), labels); axes[0].invert_yaxis()
    fig.suptitle('What changes when part of the policy is omitted?', x=.01, ha='left', fontsize=15)
    fig.savefig(out/'policy-components.png', dpi=180); fig.savefig(out/'policy-components.svg'); plt.close(fig)
    variants=['linear','tagged','reordered'];labels=['Linear text','Tagged sections','Reordered Markdown']
    fig,ax=plt.subplots(figsize=(9,4.8),constrained_layout=True)
    x=np.arange(3)
    for offset,m,color in [(-.18,'shieldstral','#2b6a91'),(.18,'qwen-4b','#be663a')]:
        reference=lookup[(m,'p0','markdown')]['accuracy']
        values=[100*(lookup[(m,'p0',v)]['accuracy']-reference) for v in variants]
        bars=ax.bar(x+offset,values,width=.34,label=names[m],color=color)
        ax.bar_label(bars,labels=[f'{v:+.1f}' for v in values],padding=4)
    ax.axhline(0,color='#697584',lw=1)
    ax.set_xticks(x,labels);ax.set_ylabel('Accuracy change from Markdown (percentage points)')
    ax.set_ylim(-4,6.5);ax.legend(frameon=False);ax.grid(axis='y',alpha=.15)
    ax.set_title('Same clauses, different presentation',loc='left',fontsize=15,pad=14)
    fig.savefig(out/'policy-format.png',dpi=180);fig.savefig(out/'policy-format.svg');plt.close(fig)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--analysis',required=True);p.add_argument('--out',required=True)
    plot(**vars(p.parse_args()))
