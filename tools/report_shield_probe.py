"""Render all frozen configurations and paired contrasts, in protocol order."""
import argparse
import json
from pathlib import Path

NAMES = {
    'primary-qwen': 'Qwen final-layer probe',
    'primary-shieldstral': 'Shieldstral final-layer probe',
    'primary-combined': 'Combined final-layer probe',
    'secondary-qwen': 'Qwen layer/pooling search',
    'secondary-shieldstral': 'Shieldstral layer/pooling search',
    'secondary-combined': 'Combined selected representations',
    'score-logistic': 'Logistic combination of output scores',
    'qwen-native': 'Qwen direct B/A score',
    'shieldstral-native': 'Shieldstral direct yes/no score',
    'score-equal-probability': 'Equal probability average',
    'score-equal-logodds': 'Equal log-odds average',
    'qwen-native-0.5': 'Qwen direct score at 0.5',
    'shieldstral-native-0.5': 'Shieldstral direct score at 0.5',
    'historical-wildguard': 'Historical WildGuard 7B',
    'historical-specialist-equal-logodds': 'Historical three-specialist score ensemble',
}


def percent(v):
    return '—' if v is None else f'{100*v:.2f}%'


def cutoff(v):
    return '0.5 (native)' if v is None else f'{v:g}'


def report(state, out):
    state = Path(state)
    r = json.loads((state/'test-results.json').read_text())
    f = json.loads((state/'freeze.json').read_text())
    fits = json.loads((state/'fits.json').read_text())
    text = ['# Full Shieldstral/Qwen representation results', '',
        'All rows use the same 1,699 test prompts: 754 harmful and 945 benign. '
        'Settings and cutoffs were selected on validation before the test pass. '
        'The tables preserve protocol order rather than ranking observed test scores.', '',
        '## Frozen balanced selections', '',
        '| Method | Representation / candidate | C | Cutoff | Validation balanced accuracy |',
        '|---|---|---:|---:|---:|']
    for group, choices in f['choices'].items():
        c = choices['balanced']; fit = fits.get(c['candidate'], {})
        reps = ' + '.join(fit.get('representation', [c['candidate']]))
        text.append(f"| {NAMES[group]} | {reps} | {fit.get('C', '—')} | {cutoff(c['threshold'])} | {percent(c['metrics']['balanced_accuracy'])} |")
    text += ['', '## Balanced operating points', '',
        '| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | Recall | False-block rate | FP | FN | Unresolved | AUROC |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for group, row in r['profiles']['balanced'].items():
        m=row['test'];lo,hi=r['ci95'][group]['balanced_accuracy']
        mcc='—' if m['mcc'] is None else f"{m['mcc']:.4f}"
        auc='—' if m.get('auroc') is None else f"{m['auroc']:.4f}"
        text.append(f"| {NAMES[group]} | {percent(m['balanced_accuracy'])} ({percent(lo)}–{percent(hi)}) | {percent(m['accuracy'])} | {percent(m['macro_f1'])} | {mcc} | {percent(m['recall'])} | {percent(m['false_positive_rate'])} | {m['false_blocks']} | {m['missed_violations']} | {m['unresolved']} | {auc} |")
    text += ['', 'Historical rows use earlier validation procedures. Direct scores condition on '
             'the canonical label pair; they are not free-generation accuracy. All new rows '
             'use this study’s fixed policy and 1,536-row validation population.', '']
    for profile, heading in [('false_block_limit','At most 5% false blocks on validation'),
                             ('catch_target','At least 90% harmful recall on validation')]:
        text += ['## '+heading, '',
            'Each profile selects its own candidate and cutoff. A validation constraint '
            'does not guarantee the same constraint on test.', '',
            '| Method | Candidate | Cutoff | Test false-block rate | Test recall | Constraint held on test? |',
            '|---|---|---:|---:|---:|---|']
        for group,row in r['profiles'][profile].items():
            if row is None:
                text.append(f'| {NAMES[group]} | No eligible validation configuration | — | — | — | — |')
                continue
            m=row['test']
            held=m['compliant_error_rate']<=.05 if profile=='false_block_limit' else m['recall']>=.9
            text.append(f"| {NAMES[group]} | {row['candidate']} | {cutoff(row['threshold'])} | {percent(m['false_positive_rate'])} | {percent(m['recall'])} | {'Yes' if held else 'No'} |")
        text += ['']
    text += ['## Prespecified paired contrasts', '',
        'Differences are balanced-accuracy percentage points. Intervals use 2,000 paired '
        'duplicate-group bootstrap samples and are descriptive, unadjusted for multiple '
        'comparisons, search or repeated public-test use.', '',
        '| Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |',
        '|---|---|---:|---:|---:|---:|']
    for p in r['paired_differences']:
        lo,hi=p['ci95']
        text.append(f"| {NAMES[p['method']]} | {NAMES[p['comparator']]} | {100*p['balanced_accuracy_delta']:+.2f} | {100*lo:+.2f} to {100*hi:+.2f} | {p['corrected']} | {p['newly_wrong']} |")
    text += ['', 'The evidence bundle also contains all category/adversarial slices, average '
        'precision, Brier scores, log loss, full confusion matrices and feature provenance. '
        '`validation.json` retains all candidate probabilities and threshold grids; '
        '`fits/` contains coefficients and scalers. Prompts and embeddings remain private.', '']
    Path(out).write_text('\n'.join(text))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();report(a.state,a.out)
