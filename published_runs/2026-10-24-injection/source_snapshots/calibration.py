"""Binary threshold selection on development data only."""
import json
from pathlib import Path
from evals.run import digest

def binary_metrics(rows):
    classes=('ALLOW','BLOCK'); f1=[]
    for label in classes:
        tp=sum(r['expected']==label and r['prediction']==label for r in rows)
        fp=sum(r['expected']!=label and r['prediction']==label for r in rows)
        fn=sum(r['expected']==label and r['prediction']!=label for r in rows)
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    return sum(f1)/2

def calibrate_binary(directory):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text())
    rows=[json.loads(s) for s in (directory/'predictions.jsonl').read_text().splitlines()]
    if m['split']!='dev' or m['mode']!='inference' or not rows or len(rows)!=len(m['selected_ids']) or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Complete development inference required')
    if any(r['split']!='dev' or 'score' not in r or r['expected'] not in ('ALLOW','BLOCK') for r in rows):
        raise ValueError('Binary development scores required')
    candidates=[]
    for t in [i/20 for i in range(1,20)]:
        pred=[dict(r,prediction='BLOCK' if r['score']>=t else 'ALLOW') for r in rows]
        candidates.append(dict(threshold=t,macro_f1=binary_metrics(pred)))
    best=max(candidates,key=lambda c:(c['macro_f1'],-abs(c['threshold']-.5),-c['threshold']))
    return dict(method='dev binary macro-F1; ties nearest 0.5 then lower threshold',selected=best,candidates=candidates,dev_predictions_sha256=digest(directory/'predictions.jsonl'))
