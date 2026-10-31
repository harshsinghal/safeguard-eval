"""Preserve every frozen profile and training seed in a readable result table."""
import argparse
import csv
import json
from pathlib import Path

def report(state,out):
    state,out=Path(state),Path(out);out.mkdir(parents=True,exist_ok=True)
    result=json.loads((state/'results.json').read_text());text=['# Frozen-feature classifier results','',
        'All choices were made on validation. Seed 20261031 is the predeclared primary '
        'neural-network run; the other two seeds are repetitions, not candidates from '
        'which to select a better test result. LR is deterministic. Tables retain '
        'protocol order. These are reused public test sets, not fresh confirmation.','']
    flat=[]
    for ds,rr in result['results'].items():
        text+=['## '+ds,'']
        for profile,table in rr['profiles'].items():
            text+=['### '+profile.replace('_',' '),'',
                '| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |',
                '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
            for name,row in table.items():
                if row is None:
                    text.append(f'| {name} | No eligible validation selection | — | — | — | — | — | — | — |');continue
                m=row['seed_metrics'][0];c=row['selection']
                text.append(f"| {name} | {c['threshold']:g} | {100*m['accuracy']:.2f}% | {100*m['balanced_accuracy']:.2f}% | {m['false_blocks']} | {m['missed_violations']} | {m['macro_f1']:.4f} | {m['mcc']:.4f} | {m['auroc']:.4f} |")
                for seed,metrics in zip(row['seeds'],row['seed_metrics']):
                    flat.append(dict(dataset=ds,profile=profile,method=name,seed=seed,candidate=c['candidate'],threshold=c['threshold'],**{k:metrics[k] for k in ['n','accuracy','balanced_accuracy','macro_f1','mcc','false_blocks','missed_violations','false_positive_rate','false_negative_rate','coverage','auroc','average_precision','brier','log_loss']}))
            text+=['']
        text+=['### Training-seed variation at the balanced setting','',
            '| Backend / head | Mean accuracy | Accuracy range | Mean balanced accuracy | Balanced accuracy range |',
            '|---|---:|---:|---:|---:|']
        for name,row in rr['profiles']['balanced'].items():
            a,b=row['summary']['accuracy'],row['summary']['balanced_accuracy']
            text.append(f"| {name} | {100*a['mean']:.2f}% | {100*a['min']:.2f}–{100*a['max']:.2f}% | {100*b['mean']:.2f}% | {100*b['min']:.2f}–{100*b['max']:.2f}% |")
        text+=['','### Paired comparisons at the balanced setting','',
            '| Method minus comparator | Balanced accuracy difference | Paired 95% interval | Change in FP | Change in FN |',
            '|---|---:|---:|---:|---:|']
        for p in rr['paired_contrasts']:
            lo,hi=p['ci95'];text.append(f"| {p['method']} minus {p['comparator']} | {100*p['balanced_accuracy_delta']:+.2f} pp | [{100*lo:+.2f}, {100*hi:+.2f}] pp | {p['false_blocks_delta']:+d} | {p['misses_delta']:+d} |")
        text+=['','Intervals use 2,000 paired duplicate-group bootstrap draws for the fixed '
            'primary seed. They are exploratory and unadjusted; they do not include '
            'training-seed, model-search, repeated-test-use or labeling uncertainty. '
            'Negative FP/FN differences mean fewer mistakes.','']
    (out/'RESULTS.md').write_text('\n'.join(text).rstrip()+'\n')
    with (out/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]),lineterminator='\n');w.writeheader();w.writerows(flat)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--out',required=True);report(**vars(p.parse_args()))
