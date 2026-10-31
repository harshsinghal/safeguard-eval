"""Render all registered profiles without choosing a winner from test scores."""
import argparse
import csv
import io
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evals.liquid_finetune.common import read


def report(state,out):
    state,out=Path(state),Path(out);out.mkdir(parents=True,exist_ok=True)
    r=read(state/'results.json');v=read(state/'validation.json');records=[]
    lines=['# Liquid classifier: complete results','',
        'WildGuard prompt harmfulness: 4,096 fitting, 1,536 validation and 1,699 test prompts.',
        'All configurations below were selected on validation before test inference. Higher is better',
        'for accuracy, balanced accuracy, F1, MCC, recall and specificity; lower is better for errors.',
        'The primary objective is ordinary accuracy. Primary seed is 20261031, not the best test seed.','',
        '| Selection objective | Pipeline | Checkpoint / C | Cutoff | Seed | Accuracy | Balanced accuracy | False blocks | Missed harmful |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for profile,table in r['profiles'].items():
        for kind,row in table.items():
            for seed,m,fixed in zip(row['seeds'],row['seed_metrics'],row['fixed_half_metrics']):
                lines.append(f'| {profile} | {kind} | {row["candidate"]} | {row["threshold"]:.2f} | {seed} | {100*m["accuracy"]:.2f}% | {100*m["balanced_accuracy"]:.2f}% | {m["false_blocks"]} | {m["missed_violations"]} |')
                for setting,threshold,values in [('validation-selected',row['threshold'],m),('fixed-half',.5,fixed)]:
                    record=dict(profile=profile,pipeline=kind,candidate=row['candidate'],seed=seed,
                                setting=setting,threshold=threshold)
                    record.update({k:val for k,val in values.items() if k!='confusion'});records.append(record)
    lines += ['','## Training variation','',
        'Fine-tuned results across all three seeds; no seed averaging is used for prediction.','',
        '| Profile | Mean accuracy | Accuracy range | Mean balanced accuracy | Balanced accuracy range |',
        '|---|---:|---:|---:|---:|']
    for profile,t in r['profiles'].items():
        a=t['finetuned']['summary']['accuracy'];b=t['finetuned']['summary']['balanced_accuracy']
        lines.append(f'| {profile} | {a["mean"]*100:.2f}% | {a["min"]*100:.2f}–{a["max"]*100:.2f}% | {b["mean"]*100:.2f}% | {b["min"]*100:.2f}–{b["max"]*100:.2f}% |')
    lines += ['','## Paired comparisons','',
        'Fine-tuned minus frozen, primary seed; percentage points. The 2,000 duplicate-group bootstrap',
        'draws hold predictions fixed. These intervals exclude seed/search uncertainty and are unadjusted.','',
        '| Profile | Accuracy difference (95% interval) | Balanced difference (95% interval) | Corrected / newly wrong |',
        '|---|---:|---:|---:|']
    for profile,c in r['paired_contrasts'].items():
        a=c['ci95']['accuracy'];b=c['ci95']['balanced_accuracy']
        lines.append(f'| {profile} | {100*c["accuracy_delta"]:+.2f} ({100*a[0]:+.2f}, {100*a[1]:+.2f}) | {100*c["balanced_accuracy_delta"]:+.2f} ({100*b[0]:+.2f}, {100*b[1]:+.2f}) | {c["corrected"]} / {c["newly_wrong"]} |')
    lines += ['','## Validation selections','',
        '| Profile | Pipeline | Selected candidate | Cutoff | Mean validation accuracy | Mean validation balanced accuracy |',
        '|---|---|---|---:|---:|---:|']
    for kind,profiles in v['choices'].items():
        for profile,row in profiles.items():
            m=row['mean_validation']
            lines.append(f'| {profile} | {kind} | {row["candidate"]} | {row["threshold"]:.2f} | {100*m["accuracy"]:.2f}% | {100*m["balanced_accuracy"]:.2f}% |')
    lines += ['','The CSV includes fixed-.5 results, precision, class F1, MCC, both error rates,',
        'coverage, AUROC, average precision, Brier and log loss for every selected seed.',
        'The evidence bundle also contains category/adversarial slices. Test results are exploratory:',
        'this public test has been used repeatedly, and pretraining contamination is not audited.','']
    (out/'RESULTS.md').write_text('\n'.join(lines))
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    (out/'results.csv').write_text(buf.getvalue())
    print('Rendered',len(records),'metric rows')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    report(**vars(p.parse_args()))
