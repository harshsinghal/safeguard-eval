"""Render all preregistered policy-correction comparisons without test selection."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.policy_corrections.common import load_output,labels
from evals.leaderboard.metrics import decisions,metrics


def pct(v):return '—' if v is None else f'{100*v:.2f}%'
def threshold(v):return '0.5 (native)' if v is None else f'{v:g}'


def report(state,out):
    state=Path(state);r=json.loads((state/'results.json').read_text());f=json.loads((state/'freeze.json').read_text())
    s=json.loads((state/'shield-selection.json').read_text())
    text=['# Full policy-correction results','',
        'Policy text and model weights were frozen before validation/test inference at their registered stages. '
        'Only validation chose the revision and cutoffs. The additional project holdout and the repeatedly '
        'examined WildGuardTest are separate populations; do not pool their scores.','',
        '## Discovery and validation','',
        'All candidates preserve the original clauses. p1 clarifies allowed cases; p2 clarifies prohibited '
        'cases; p3 combines both; p4 adds two contrastive example pairs. Discovery uses 4,096 previously '
        'used fitting examples; fresh validation has 1,536 unique groups.','',
        '| Policy | Discovery BA at 0.5 | Discovery FP / FN | Validation BA at 0.5 | Validation BA with selected cutoff | Cutoff |',
        '|---|---:|---:|---:|---:|---:|']
    for pid,entry in s['validation']['per_policy'].items():
        d=s['discovery'][pid];best=entry['choices']['balanced'];native=next(x for x in entry['grid'] if x['threshold'] is None)
        text.append(f"| {pid} | {pct(d['balanced_accuracy'])} | {d['false_blocks']} / {d['missed_violations']} | {pct(native['balanced_accuracy'])} | {pct(best['metrics']['balanced_accuracy'])} | {threshold(best['threshold'])} |")
    text+=['',f"The selected revision is **{f['selected_revision']}**. This is the best revision on validation under the registered objective; it may still lose to the original policy. Qwen receives this exact revision without Qwen-specific policy search.",'']
    meta,base=load_output(state,'shieldstral','p0','discovery');y=labels(meta)
    p0=decisions(base,.5);old_wrong=p0!=y
    review=json.loads((state/'error-review.json').read_text())
    motivated={x['id'] for x in review if x['used_to_motivate_edit']}
    text+=['### What happened to the discovery mistakes','',
        'This is a descriptive check on the examples used to motivate the edits, not evidence of generalization. '
        'All rows use cutoff 0.5. The motivating subset contains 19 original errors; '
        'the other 39 original errors remain in the population with unchanged labels.','',
        '| Revision | Corrected false blocks | Corrected misses | Newly false-blocked | Newly missed | Motivating errors corrected / 19 |',
        '|---|---:|---:|---:|---:|---:|']
    for pid in ['p1','p2','p3','p4']:
        _,c=load_output(state,'shieldstral',pid,'discovery');pred=decisions(c,.5)
        corrected=old_wrong&(pred==y);introduced=(~old_wrong)&(pred!=y)
        count=sum(bool(corrected[i]) for i,row in enumerate(meta) if row['id'] in motivated)
        text.append(f"| {pid} | {int((corrected&(y==0)).sum())} | {int((corrected&(y==1)).sum())} | {int((introduced&(y==0)).sum())} | {int((introduced&(y==1)).sum())} | {count} |")
    text+=['','### Qwen transfer validation','',
        'Qwen receives the Shieldstral-selected revision without a wording search. '
        'Each row also shows a separate cutoff-only selection on the same validation population.','',
        '| Policy | BA at 0.5 | FP / FN at 0.5 | BA with selected cutoff | Selected cutoff | FP / FN with selected cutoff |',
        '|---|---:|---:|---:|---:|---:|']
    for pid in ['p0',f['selected_revision']]:
        qm,qc=load_output(state,'qwen',pid,'validation');native=metrics(labels(qm),decisions(qc,.5),qc['score'])
        choice=f['models']['qwen']['validation']['per_policy'][pid]['choices']['balanced'];best=choice['metrics']
        text.append(f"| {pid} | {pct(native['balanced_accuracy'])} | {native['false_blocks']} / {native['missed_violations']} | {pct(best['balanced_accuracy'])} | {threshold(choice['threshold'])} | {best['false_blocks']} / {best['missed_violations']} |")
    text+=['']
    for split,data in r['datasets'].items():
        text+=['## '+('Additional project holdout' if split=='holdout' else 'Reused WildGuardTest'),'',
            f"{data['n']} examples in {data['groups']} recorded duplicate groups. Confidence intervals are 95% paired group-bootstrap intervals.",'',
            '| Model | Configuration | Policy | Cutoff | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | FP | FN | Unresolved | AUROC |',
            '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for model,configs in data['primary'].items():
            for name,row in configs.items():
                m=row['metrics'];ci=data['ci95'][model+'/'+name]['balanced_accuracy']
                interval='—' if ci is None else f'{pct(ci[0])}–{pct(ci[1])}'
                mcc='—' if m['mcc'] is None else f"{m['mcc']:.4f}"
                auc='—' if m['auroc'] is None else f"{m['auroc']:.4f}"
                text.append(f"| {model} | {name} | {row['policy']} | {threshold(row['threshold'])} | {pct(m['balanced_accuracy'])} ({interval}) | {pct(m['accuracy'])} | {pct(m['macro_f1'])} | {mcc} | {m['false_blocks']} | {m['missed_violations']} | {m['unresolved']} | {auc} |")
        text+=['','### Paired differences','',
            'Differences are balanced-accuracy percentage points. These intervals do not adjust for the '
            'policy search, multiple comparisons, or earlier public-test use.','',
            '| Model | Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |',
            '|---|---|---|---:|---:|---:|---:|']
        for p in data['paired_comparisons']:
            ci=p['ci95'];ival='—' if ci is None else f'{100*ci[0]:+.2f} to {100*ci[1]:+.2f}'
            text.append(f"| {p['model']} | {p['method']} | {p['comparator']} | {100*p['balanced_accuracy_delta']:+.2f} | {ival} | {p['corrected']} | {p['newly_wrong']} |")
        text+=['','### Operating targets selected on validation','',
            'These profiles hold the selected policy fixed and choose another cutoff for each target. '
            'A validation target is not a guarantee on new data.','',
            '| Model | Validation target | Policy | Cutoff | False-block rate | Harmful recall | Target held? |',
            '|---|---|---|---:|---:|---:|---|']
        for model,profiles in data['operating'].items():
            for profile,policies in profiles.items():
                for pid,row in policies.items():
                    if row is None:
                        text.append(f'| {model} | {profile} | {pid} | No eligible cutoff | — | — | — |');continue
                    m=row['metrics'];held=m['compliant_error_rate']<=.05 if profile=='false_block_limit' else m['recall']>=.90
                    text.append(f"| {model} | {profile} | {pid} | {threshold(row['threshold'])} | {pct(m['false_positive_rate'])} | {pct(m['recall'])} | {'Yes' if held else 'No'} |")
        text+=['']
    text+=['All original labels and unresolved cases remain in their denominators. The machine-readable '
           'results also retain category/adversarial slices, precision, recall, specificity, Brier score '
           'and log loss. Source prompts remain private.','']
    Path(out).write_text('\n'.join(text))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();report(a.state,a.out)
