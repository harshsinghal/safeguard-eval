"""Verify saved predictions and build a static leaderboard. No inference or network."""
import argparse,json,random,statistics,hashlib,shutil
from pathlib import Path
from evals.run import metrics,load_cases,digest,parse_response,score_decision
from evals.injection.calibration import binary_metrics,calibrate_binary
from evals.calibrate import calibrate
MODELS={'safeguard':'GPT-OSS Safeguard 20B','policylm':'PolicyLM 1.7B','cope':'CoPE-B-A4B','shieldstral':'Shieldstral 3B'}

def score(rows,track):
    m=metrics(rows)
    if track=='deepset':m['macro_f1']=binary_metrics(rows)
    return m

def interval(rows,track):
    # Resample scenario groups for challenge; individual independent rows for deepset.
    rng=random.Random(20261024); groups={}
    for r in rows:groups.setdefault(r['group'],[]).append(r)
    keys=sorted(groups);values=[]
    for _ in range(2000):
        sample=[r for k in rng.choices(keys,k=len(keys)) for r in groups[k]]
        values.append(score(sample,track)['macro_f1'])
    values.sort();return [values[49],values[1949]]

def build(root,site):
    records=[];examples={}
    for track in ('deepset','challenge'):
        data=load_cases(root/'data'/f'{track}.jsonl'); gold={r['id']:r for r in data if r['split']=='test'}
        examples[track]=[{**r,'models':{}} for r in gold.values()]
        index={r['id']:r for r in examples[track]}
        notes=json.loads(Path('evals/injection/review_notes.json').read_text())['notes']
        for ident,note in notes.items():
            if ident in index:index[ident]['annotation_note']=note
        for adapter,name in MODELS.items():
            d=root/f'{adapter}-{track}-test';manifest=json.loads((d/'manifest.json').read_text())
            rows=[json.loads(s) for s in (d/'predictions.jsonl').read_text().splitlines()]
            if adapter!='safeguard':
                dev=root/f'{adapter}-{track}-dev'
                calibration=json.loads((dev/'calibration.json').read_text())
                recalculated=calibrate_binary(dev) if track=='deepset' else calibrate(dev)
                assert calibration==recalculated
                selected=calibration['selected']
                expected_thresholds=([selected['threshold']]*2 if track=='deepset' else [selected['allow_below'],selected['block_at']])
                assert [manifest['allow_below'],manifest['block_at']]==expected_thresholds
            assert set(manifest['selected_ids'])==set(gold)=={r['id'] for r in rows}
            assert len(rows)==len(gold)
            assert manifest['runner_sha256']==digest(root/'source_snapshots'/'run.py')
            saved=json.loads((d/'summary.json').read_text())
            assert all(saved[k]==v for k,v in metrics(rows).items())
            assert manifest['dataset_sha256']==digest(root/'data'/f'{track}.jsonl')
            assert manifest['policy_sha256']==digest(root/'data'/('binary-policy.json' if track=='deepset' else 'policy.json'))
            for r in rows:
                assert r['expected']==gold[r['id']]['expected'] and r['prompt']==gold[r['id']]['prompt']
                if r['prediction']!='ERROR':
                    dec=(score_decision(r['score'],manifest['allow_below'],manifest['block_at']) if adapter=='policylm' else parse_response({'choices':r['raw_output']},adapter,manifest['allow_below'],manifest['block_at'])['decision'])
                    assert dec==r['prediction']
                index[r['id']]['models'][adapter]={k:r[k] for k in ('prediction','score','reason','latency_seconds') if k in r}
            m=score(rows,track);m['macro_f1_ci95']=interval(rows,track)
            m['latency_median_ms']=1000*statistics.median(r['latency_seconds'] for r in rows)
            records.append(dict(adapter=adapter,model=name,track=track,metrics=m,thresholds=[manifest['allow_below'],manifest['block_at']],artifact=f'https://github.com/harshsinghal/safeguard-eval/tree/main/{root.as_posix()}/{d.name}'))
    result=dict(title='Policy Model Arena',run='2026-10-24',records=records,examples=examples,billing=json.loads((root/'billing.json').read_text()) if (root/'billing.json').exists() else None)
    site.mkdir(exist_ok=True);(site/'leaderboard.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (root/'leaderboard-summary.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ('model','track','metrics')} for r in records],indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--site',type=Path,default=Path('site'));a=p.parse_args();build(a.run,a.site)
