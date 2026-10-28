"""Render frozen ensemble results. This module never fits or selects a model."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from evals.ensemble.common import COHORTS, read, write

TITLES = {'wildguard-specialists': 'WildGuard · 3 specialists',
          'hatexplain-specialists': 'HateXplain · 2 specialists',
          'hatexplain-mixed': 'HateXplain · specialists + Qwen'}
METHODS = [('single', 'Selected individual'), ('equal-raw', 'Equal average'),
           ('equal-calibrated', 'Calibrated average'), ('weighted', 'Learned weighted average'),
           ('logistic', 'Logistic regression'), ('forest', 'Random forest')]


def build(state, destination):
    state, destination = Path(state), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    figures = destination / 'figures'; figures.mkdir(exist_ok=True)
    all_results = {name: read(state/'cohorts'/name/'results.json') for name in COHORTS}
    lines = ['# Complete ensemble results', '',
             'Every family below was registered before fitting. Its configuration and blocking threshold were selected on validation accuracy, with macro-F1 as the first tie-break. Logistic regression was the primary method. All scores are percentages; differences are percentage points.', '',
             'Test results are exploratory because these official tests were used in earlier studies. Intervals are unadjusted paired group-bootstrap intervals (2,000 replicates), not corrections for multiple comparisons or model-selection uncertainty.', '']
    summaries = {}
    for cohort, r in all_results.items():
        selection = read(state/'cohorts'/cohort/'selection.json')
        lines += [f'## {TITLES[cohort]}', '', f"Test examples: **{r['n']:,}**. Validation-selected ensemble: `{r['best_ensemble']}`. Validation-selected individual: `{r['best_single']}`.", '',
                  '| Method | Test accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |',
                  '|---|---:|---:|---:|---:|---:|']
        chosen = [('WildGuard model', 'wildguard-baseline')] if 'wildguard-baseline' in r['all_candidates'] else []
        chosen += [(label, r['selection'][family]) for family, label in METHODS]
        for label, cid in chosen:
            m = r['all_candidates'][cid]['metrics']
            lines.append(f"| {label} | {100*m['accuracy']:.2f} | {100*m['macro_f1']:.2f} | {100*m['violation_recall']:.2f} | {m['false_blocks']} | {m['missed_violations']} |")
        lines += ['', 'The comparison below is against the individual selected on validation, including its calibration/threshold tuning.', '',
                  '| Ensemble | Accuracy difference | 95% interval | Cases corrected | Cases made wrong |',
                  '|---|---:|---:|---:|---:|']
        for family, label in METHODS[1:]:
            c = r['contrasts'][family]['vs_best_single']; lo, hi = c['accuracy_ci95']
            lines.append(f"| {label} | {100*c['accuracy_delta']:+.2f} | {100*lo:+.2f} to {100*hi:+.2f} | {c['cases_fixed']} | {c['cases_broken']} |")
        lines += ['', '### Individual-model controls', '',
                  '| Model | Raw score at 0.5: accuracy | Validation-selected individual: accuracy | Selected threshold / configuration |',
                  '|---|---:|---:|---|']
        for model, cid in r['per_model_selected'].items():
            raw = r['all_candidates'][f'single/{model}/fixed']['metrics']['accuracy']
            tuned = r['all_candidates'][cid]
            lines.append(f"| {model} | {100*raw:.2f} | {100*tuned['metrics']['accuracy']:.2f} | {tuned['threshold']:.2f} / `{cid}` |")
        lines += ['', 'A threshold on a calibrated score is not the same numerical threshold on the raw score. Monotonic single-model calibration changes the decision boundary, not the order of examples.', '',
                  '### Frozen choices', '', '| Family | Candidate | Validation accuracy | Threshold |', '|---|---|---:|---:|']
        for family, _ in METHODS:
            c = next(x for x in selection['candidates'] if x['id'] == r['selection'][family])
            lines.append(f"| {family} | `{c['id']}` | {100*c['validation']['accuracy']:.2f} | {c['selected_threshold']:.2f} |")
        weighted = next(x for x in selection['candidates'] if x['id'] == r['selection']['weighted'])
        weights = dict(zip(selection['feature_names'], weighted['weights']))
        lines += ['', 'Learned averaging weights: ' + ', '.join(f'{k} {100*v:.2f}%' for k, v in weights.items()) + '.', '',
                  '### Complementary errors', '', '| Pair | Disagreements | Both wrong | First correct, second wrong | Second correct, first wrong |', '|---|---:|---:|---:|---:|']
        for p in r['complementarity']:
            lines.append(f"| {p['a']} / {p['b']} | {p['disagreements']} | {p['both_wrong']} | {p['a_correct_b_wrong']} | {p['b_correct_a_wrong']} |")
        lines += ['', f"A hindsight rule that could choose a correct individual whenever one existed would reach {100*r['hindsight_label_oracle']['accuracy']:.2f}%. It uses the answer key and cannot be deployed. It is not an upper bound on ensembles that use continuous scores.", '',
                  f"The highest test accuracy among all registered individual configurations was {100*r['highest_observed_test_single']['accuracy']:.2f}%. This is a descriptive hurdle, not a test-based selector.", '',
                  'All candidate metrics, binary confusion matrices, category/platform/annotation-agreement slices and per-example decisions are retained in the cohort evidence. Single-label slices should be interpreted using counts and recall, not their two-class macro-F1.', '']
        summaries[cohort] = dict(n=r['n'], primary=r['primary'], best_single=r['best_single'],
            best_ensemble=r['best_ensemble'], selected={label:r['all_candidates'][cid]['metrics'] for label,cid in chosen},
            contrasts=r['contrasts'], weights=weights)
    (destination/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    write(destination/'summary.json', summaries)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.8))
    colors = ['#60728A','#A9B9CC','#A9B9CC','#269A8B','#175C9C','#D79739']
    for ax, (cohort, r) in zip(axes, all_results.items()):
        values = [100*r['all_candidates'][r['selection'][family]]['metrics']['accuracy'] for family,_ in METHODS]
        ys = np.arange(len(METHODS)); ax.barh(ys,values,color=colors,height=.6)
        ax.set_yticks(ys,[label for _,label in METHODS]); ax.invert_yaxis()
        ax.set_xlim(0,105); ax.set_xticks([0,25,50,75,100]); ax.set_xlabel('Test accuracy (%)')
        ax.set_title(TITLES[cohort],fontsize=11,fontweight='bold',pad=12)
        for y, value in zip(ys, values): ax.text(value+1,y,f'{value:.2f}',va='center',fontsize=10)
        ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('Combining models did not consistently beat a calibrated individual',fontsize=17,fontweight='bold',y=.99)
    fig.text(.02,.03,'Configurations selected on validation. Logistic regression was primary; all registered families are shown.\nWildGuard: 1,699 test prompts. HateXplain: 1,924 posts. Reused official tests; exploratory results.',fontsize=10,color='#475569')
    fig.tight_layout(rect=(0,.13,1,.93),w_pad=2)
    for ext in ['png','svg']: fig.savefig(figures/f'accuracy.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13.5,5.2))
    for ax,(cohort,r) in zip(axes,all_results.items()):
        for i,(family,label) in enumerate(METHODS[1:]):
            c=r['contrasts'][family]['vs_best_single'];point=100*c['accuracy_delta'];lo,hi=np.array(c['accuracy_ci95'])*100
            ax.errorbar(point,i,xerr=[[max(0,point-lo)],[max(0,hi-point)]],fmt='o',color=colors[i+1],capsize=4,markersize=6)
        ax.axvline(0,color='#6B7280',linestyle='--',linewidth=1);ax.invert_yaxis()
        ax.set_yticks(range(5),[label for _,label in METHODS[1:]])
        ax.set_title(TITLES[cohort],fontsize=11,fontweight='bold',pad=12)
        ax.set_xlabel('Accuracy difference (percentage points)');ax.grid(axis='x',alpha=.15)
    fig.suptitle('Accuracy gains are small or absent after a fair single-model comparison',fontsize=16,fontweight='bold',y=.99)
    fig.text(.02,.025,'Relative to the validation-selected individual within each cohort. Bars: unadjusted 95% paired group-bootstrap intervals.\nIntervals exclude policy-search and inference uncertainty. They do not adjust for the number of methods compared.',fontsize=10,color='#475569')
    fig.tight_layout(rect=(0,.14,1,.92),w_pad=2)
    for ext in ['png','svg']:fig.savefig(figures/f'paired-differences.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();build(a.state,a.destination)
