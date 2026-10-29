"""Archive new outputs and extend the frozen leaderboard without reselection."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import shutil

import numpy as np

from evals.decision_models.study import MODELS, predictions, sources, verify_freeze
from evals.jev.api import hash_value
from evals.jev.study import DATA, IDS
from evals.leaderboard.archive import digest, normalize, read, write
from evals.leaderboard.build import score_bundle, exports
from evals.leaderboard.metrics import decisions, metrics
from evals.leaderboard.render import render

LABELS={'kev':'Kev 4B','clef':'Clef-Flash 9B'}


def archive(state, destination):
    state=Path(state); destination=Path(destination)
    f=verify_freeze(state)
    if destination.exists(): raise ValueError('Use a new archive destination')
    destination.mkdir(parents=True)
    for rel in ('registration.json','freeze.json','PLAN.md'):
        shutil.copy2(state/rel,destination/rel)
    for slug in MODELS:
        for rel in ('policies-freeze.json','parity.json','development-environment.json','test-environment.json'):
            p=destination/slug/rel; p.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(state/slug/rel,p)
        for ds in DATA:
            shutil.copytree(state/'policies'/slug/ds,destination/'policies'/slug/ds)
            for split in ('fit','validation','test'):
                for pid in (('brief','detailed') if split=='fit' else IDS):
                    rr=predictions(state,slug,ds,split,pid)
                    if any('prompt' in r for r in rr): raise ValueError('Raw prompts in public prediction archive')
                    dest=destination/'predictions'/slug/ds/split/(pid+'.jsonl.gz')
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(gzip.compress(('\n'.join(json.dumps(r,ensure_ascii=False,allow_nan=False) for r in rr)+'\n').encode(),mtime=0))
    root=Path(__file__).resolve().parents[2]
    for rel in sources():
        dest=destination/'source'/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/rel,dest)
    for rel in ('evals/decision_models/report.py','evals/decision_models/fetch_sources.py','tests/test_decision_models.py'):
        dest=destination/'source'/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/rel,dest)
    return f


def extend(state, prior, bundle, experiment):
    state=Path(state); prior=Path(prior); bundle=Path(bundle); experiment=Path(experiment)
    f=verify_freeze(state)
    if bundle.exists(): raise ValueError('Use a new leaderboard destination')
    bundle.mkdir(parents=True)
    old_checks=read(prior/'checksums.json')['sha256']
    for rel,h in old_checks.items():
        if digest(prior/rel)!=h: raise ValueError('Prior evidence changed: '+rel)
    specs=read(prior/'registry.json'); selection=read(prior/'selection.json'); coverage=read(prior/'coverage.json')
    variants={}
    for ds in DATA:
        for split in ('validation','test'):
            data=read(prior/split/(ds+'.json.gz'))
            for slug in MODELS:
                pp=read(state/'policies'/slug/ds/'final.json')
                for pid in IDS:
                    cid=f'{ds}/decision-models/{slug}/{pid}'
                    rr=predictions(state,slug,ds,split,pid)
                    data['candidates'][cid]=normalize(data['metadata'],rr)
                    specs[cid]=dict(id=cid,dataset=ds,group=slug,model=slug,label=LABELS[slug],category='Typed classifier',
                        model_id=MODELS[slug]['id'],revision=MODELS[slug]['revision'],policy=pid,policy_sha256=hash_value(pp[pid]),
                        adapter='Native Choice / released decision head',variant='BF16; instructions + criteria',kind='raw',
                        source_archive=experiment.name,fitting_rows=1024,validation_rows=DATA[ds]['validation'][1])
            write(bundle/split/(ds+'.json.gz'),data)
        for slug in MODELS:
            choices=copy.deepcopy(f['selections'][slug+'/'+ds])
            for c in choices.values():
                if c: c['candidate']=f'{ds}/decision-models/{slug}/'+c['candidate']
            selection[ds][slug]=dict(choices=choices,candidates=3)
            test=read(bundle/'test'/(ds+'.json.gz')); y=np.array([int(r['expected']=='BLOCK') for r in test['metadata']])
            variants[slug+'/'+ds]={}
            for pid in IDS:
                value=test['candidates'][f'{ds}/decision-models/{slug}/{pid}']
                chosen=f['per_policy'][slug+'/'+ds][pid]['balanced']
                variants[slug+'/'+ds][pid]=dict(native=metrics(y,value['prediction'],value['score']),
                    validation_selected_threshold=chosen['threshold'],validation=chosen['metrics'],
                    tuned=metrics(y,decisions(value,chosen['threshold']),value['score']))
                if pid!='examples':
                    fit=predictions(state,slug,ds,'fit',pid)
                    variants[slug+'/'+ds][pid]['fitting_native']=metrics(
                        [int(r['expected']=='BLOCK') for r in fit],
                        [{'ALLOW':0,'BLOCK':1,'ERROR':-1}[r['prediction']] for r in fit],
                        [r['score'] for r in fit])
    for slug in MODELS:
        coverage['models'].append(dict(model=LABELS[slug],model_id=MODELS[slug]['id'],category='Typed classifier',
            wildguard='full test',hatexplain='full test'))
    coverage['candidate_counts']={ds:sum(s['dataset']==ds for s in specs.values()) for ds in DATA}
    coverage['historical_results']['decision-models']=f'published_runs/{experiment.name}/README.md'
    for rel,obj in [('registry.json',specs),('selection.json',selection),('coverage.json',coverage)]: write(bundle/rel,obj)
    write(experiment/'policy-contrasts.json',variants)
    artifacts=['registry.json','selection.json','coverage.json']+[f'validation/{ds}.json.gz' for ds in DATA]
    write(bundle/'freeze.json',dict(created_utc=f['created_utc'],status='new entries selected before new inference on test',
        analysis_role='exploratory extension; previous entries unchanged; public tests reused',primary='balanced_accuracy',
        expected_test_n={ds:DATA[ds]['test'][1] for ds in DATA},
        artifact_hashes={p:digest(bundle/p) for p in artifacts},
        prior_archive=prior.name,prior_checksums_sha256=digest(prior/'checksums.json'),
        decision_freeze_sha256=digest(state/'freeze.json'),note='Prior selections copied unchanged. No fitting in this extension.'))
    shutil.copy2(state/'PLAN.md',bundle/'PLAN.md')
    results=score_bundle(bundle); write(bundle/'results.json',results); exports(bundle,results); render(bundle)
    p=bundle/'RESULTS.md'; p.write_text(p.read_text().replace(
        'Retrospective reanalysis of saved outputs. Choices were selected on the common validation set, then frozen before this analysis scored the already-observed official tests. No new inference or fitting.',
        'Exploratory extension with new Kev and Clef inference. Their policies and cutoffs were frozen on validation before test inference. All 18 earlier entries retain their previous selections. No model weights or combiners were trained. The public tests were already used in earlier studies.'))
    p=bundle/'index.html'; p.write_text(p.read_text().replace(
        'No new API calls, GPU rentals, or model fitting were used to build this leaderboard.',
        'This extension adds frozen-weight Kev and Clef inference on a rented GPU. Earlier entries and selections remain unchanged. No model weights or combiners were trained.').replace(
        'ensembles, and Jev.', 'ensembles, Jev, Kev, and Clef.'))
    shutil.copytree(prior/'source',bundle/'source')
    shutil.copy2(prior/'requirements.txt',bundle/'requirements.txt')
    old_results=read(prior/'results.json')
    for ds in DATA:
        for profile,view in old_results['datasets'][ds]['profiles'].items():
            by_group={r['group']:r for r in results['datasets'][ds]['profiles'][profile]['rows']}
            for r in view['rows']:
                if {k:v for k,v in r.items() if k!='rank'}!={k:v for k,v in by_group[r['group']].items() if k!='rank'}:
                    raise ValueError('An earlier leaderboard entry changed')
    write(bundle/'extension-provenance.json',dict(prior=prior.name,experiment=experiment.name,
        previous_entries_unchanged=True,prior_checksums_sha256=digest(prior/'checksums.json')))
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--prior',required=True)
    p.add_argument('--experiment',required=True);p.add_argument('--leaderboard',required=True);a=p.parse_args()
    archive(a.state,a.experiment);extend(a.state,a.prior,a.leaderboard,a.experiment)
