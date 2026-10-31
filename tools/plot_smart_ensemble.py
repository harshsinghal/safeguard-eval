"""Plot frozen error rates; does not select methods or call model providers."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def plot(source, output):
    results = json.loads(Path(source).read_text())['datasets']
    methods = ['best-individual', 'equal-logodds', 'primary',
               'all-logistic', 'nonlinear', 'open-only']
    labels = ['Best individual\n(selected on validation)', 'All models: equal log-odds',
              'Training-selected system', 'All-model logistic',
              'Shallow gradient boosting', 'Open-only selection']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.fonttype': 'none', 'axes.spines.top': False,
                         'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True)
    for ax, (ds, title) in zip(axes, [('wildguard', 'WildGuardTest · 1,699 prompts'),
                                    ('hatexplain', 'HateXplain · 1,924 posts')]):
        rows = [results[ds]['methods'][m]['balanced']['metrics'] for m in methods]
        ax.axhspan(1.55, 2.45, color='#f0f5f8', zorder=0)
        y = np.arange(len(methods))
        for offset, key, color, label in [(-.18, 'false_positive_rate', '#206c83', 'False blocks / compliant cases'),
                                          (.18, 'false_negative_rate', '#c37a27', 'Misses / violation cases')]:
            values = [100*r[key] for r in rows]
            ax.barh(y+offset, values, height=.31, color=color, label=label)
            for yy, v in zip(y+offset, values):
                ax.text(v+.35, yy, f'{v:.1f}%', va='center', fontsize=9)
        ax.set_title(title, loc='left', fontweight='bold', pad=17)
        ax.set_yticks(y, labels)
        ax.set_xlabel('Error rate (%) — lower is better')
        ax.set_xlim(0, max(max(100*r[k] for r in rows) for k in ['false_positive_rate', 'false_negative_rate'])+5)
        ax.xaxis.grid(True, alpha=.15)
        ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    handles, legend = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend, loc='upper center', ncol=2, frameon=False, bbox_to_anchor=(.6, 1.01))
    unresolved = sum(results[d]['methods'][m]['balanced']['metrics']['unresolved'] for d in results for m in methods)
    coverage = 'All displayed methods resolved every test case.' if unresolved == 0 else 'See tables for unresolved cases, counted as errors.'
    fig.text(.025, .015, 'Validation-selected cutoffs; reused public tests. ' + coverage, fontsize=9, color='#555555')
    fig.tight_layout(rect=[0, .055, 1, .93], w_pad=3)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches='tight')
    if output.suffix == '.svg':
        output.write_text('\n'.join(line.rstrip() for line in output.read_text().splitlines()) + '\n')
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--results', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    plot(args.results, args.output)
