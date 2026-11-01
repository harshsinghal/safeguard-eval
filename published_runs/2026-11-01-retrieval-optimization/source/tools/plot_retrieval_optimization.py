"""Plot frozen retrieval choices from saved results; no inference calls."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np


def plot(results, output):
    data = json.loads(Path(results).read_text())
    models = [('policylm', 'PolicyLM 1.7B'), ('shieldstral', 'Shieldstral 3B'),
              ('kev', 'Kev 4B'), ('jev', 'Jev 1.14')]
    roles = [('policy_only', 'Policy alone', '#667085', 'o'),
             ('original_nearest', 'Original retrieval', '#b7791f', 's'),
             ('retrieval_selected', 'Selected retrieval', '#2563a6', 'D'),
             ('system_selected', 'Selected overall', '#28765c', 'o')]
    fig, ax = plt.subplots(figsize=(11, 7.5))
    fig.patch.set_facecolor('white')
    values = []
    for i, (model, name) in enumerate(models):
        center = (len(models) - 1 - i) * 1.6
        for j, (role, label, color, marker) in enumerate(roles):
            cid = data['roles'][model][role]
            value = 100 * data['test'][model][cid]['accuracy']
            values.append(value)
            y = center + .45 - .3 * j
            ax.scatter(value, y, color=color, marker=marker, s=62, zorder=3,
                       label=label if i == 0 else None)
            ax.annotate(f'{value:.2f}%', (value, y), xytext=(8, 0),
                        textcoords='offset points', va='center', fontsize=10, color='#243247')
        if i < len(models) - 1:
            ax.axhline(center - .8, color='#e5e7eb', linewidth=.8)
    lo, hi = np.floor(min(values)) - 1, np.ceil(max(values)) + 2
    ax.set_xlim(lo, hi)
    ax.set_ylim(-.85, 5.75)
    ax.set_yticks([4.8, 3.2, 1.6, 0], [name for _, name in models], fontsize=11)
    ax.tick_params(axis='y', length=0, pad=18)
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlabel('Accuracy on 1,699 WildGuardTest prompts', fontsize=11, labelpad=12)
    ax.grid(axis='x', color='#eef0f3', linewidth=.8)
    ax.set_axisbelow(True)
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('#c8cdd6')
    ax.legend(loc='lower left', bbox_to_anchor=(-.02, 1.01), ncol=4,
              frameon=False, fontsize=10, columnspacing=1.3, handletextpad=.5)
    fig.text(.04, .96, 'Does better retrieval improve moderation?', fontsize=20,
             weight='bold', color='#172c49')
    fig.text(.04, .916, 'Choices were made on validation data before these test predictions.',
             fontsize=11, color='#475467')
    fig.text(.04, .035, 'Selected overall can choose no examples. Identical configurations share predictions.\n'
             'Model weights and decision cutoffs stayed fixed. The reused public test makes this exploratory evidence.',
             fontsize=10, color='#475467', linespacing=1.5)
    fig.subplots_adjust(left=.2, right=.96, bottom=.16, top=.82)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True)
    parser.add_argument('--output', required=True)
    plot(**vars(parser.parse_args()))
