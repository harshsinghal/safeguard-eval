"""Recompute every published selection, operating point and paired interval."""
import argparse
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.activation_probe.common import read, labels, PRIMARY, write, now
from evals.activation_probe.study import check_freeze, score_metrics
from evals.leaderboard.metrics import select, decisions, bootstrap


def verify(state):
    state=Path(state);freeze=check_freeze(state)
    val=read(state/'validation.json');fits=read(state/'fits.json')
    yv=labels(val['metadata']);groups={}
    for model in ('qwen','policylm'):
        groups['primary-'+model]=[k for k,v in fits.items() if v['representation']==[PRIMARY[model]]]
        groups['secondary-'+model]=[k for k,v in fits.items()
                                     if len(v['representation'])==1 and v['representation'][0].startswith(model+'-')]
    for group,reps in [('primary-combined',[PRIMARY['qwen'],PRIMARY['policylm']]),
                       ('secondary-combined',freeze['secondary_combined_representations'])]:
        groups[group]=[k for k,v in fits.items() if v['representation']==reps]
    groups['policylm-native']=['policylm-native']
    for group,ids in groups.items():
        choices,grid=select(yv,{i:val['candidates'][i] for i in ids})
        if choices!=freeze['choices'][group] or choices!=val['choices'][group]:
            raise ValueError('Selection differs: '+group)
        if grid!=val['grids'][group]:raise ValueError('Validation grid differs: '+group)
    test=read(state/'test-predictions.json');result=read(state/'test-results.json');y=labels(test['metadata'])
    for profile,rr in result['profiles'].items():
        for group,row in rr.items():
            if row is None or group.startswith('historical-'):continue
            c=test['candidates'][row['candidate']];p=decisions(c,row['threshold'])
            s=np.asarray([np.nan if x is None else x for x in c['score']])
            m=score_metrics(y,p,s)
            # The fixed-cutoff continuity control intentionally reports no calibration metrics.
            if group=='policylm-native-0.5':m.pop('brier',None);m.pop('log_loss',None)
            if m!=row['test']:raise ValueError('Test metrics differ: '+profile+'/'+group)
    predictions={k:np.asarray(p) for k,p in test['balanced_predictions'].items()}
    b=bootstrap(test['metadata'],predictions)
    ci={g:{k:[float(v) for v in np.nanquantile(a,[.025,.975])] for k,a in mm.items()} for g,mm in b.items()}
    if ci!=result['ci95']:raise ValueError('Confidence intervals differ')
    for pair in result['paired_differences']:
        g,o=pair['method'],pair['comparator']
        interval=[float(v) for v in np.quantile(b[g]['balanced_accuracy']-b[o]['balanced_accuracy'],[.025,.975])]
        if interval!=pair['ci95']:raise ValueError('Paired interval differs')
        if int(((predictions[g]==y)&(predictions[o]!=y)).sum())!=pair['corrected']:
            raise ValueError('Corrected case count differs')
        if int(((predictions[g]!=y)&(predictions[o]==y)).sum())!=pair['newly_wrong']:
            raise ValueError('New error count differs')
    for field,ss in result['slices'].items():
        for value,rr in ss.items():
            mask=np.asarray([str(r.get(field))==value for r in test['metadata']])
            from evals.leaderboard.metrics import metrics
            if {g:metrics(y[mask],p[mask]) for g,p in predictions.items()}!=rr:
                raise ValueError('Slice metrics differ')
    report=dict(verified_utc=now(),selection_groups=len(groups),profiles=len(result['profiles']),
                paired_comparisons=len(result['paired_differences']),
                candidate_fits=len(fits),bootstrap_repetitions=2000,
                checks=['validation grids and selections','all test operating points',
                        'paired group-bootstrap intervals','corrected/new error counts','all slices'])
    write(state/'verification.json',report);print(report)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True)
    verify(p.parse_args().state)
