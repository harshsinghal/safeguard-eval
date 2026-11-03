"""Candidate registry, validation selection and immutable holdout freeze."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from evals.wildguard.run import digest, read_rows
from evals.wildguard.metrics import metrics, calibrate

POLICY_MODELS=('policylm','shieldstral','cope','safeguard')


def verified_run(path,split,adapter,policy_hash):
    path=Path(path)
    m=json.loads((path/'manifest.json').read_text())
    if m['split']!=split or m['adapter']!=adapter or m['policy_sha256']!=policy_hash:
        raise ValueError('Run identity or partition mismatch: '+str(path))
    rows=[json.loads(x) for x in (path/'predictions.jsonl').read_text().split('\n') if x.strip()]
    if len(rows)!=len(m['ids']) or {r['id'] for r in rows}!=set(m['ids']) or {r['split'] for r in rows}!={split}:
        raise ValueError('Incomplete or wrong-partition predictions: '+str(path))
    return m,metrics(rows)


def select(registry,run_root):
    """Registry candidates must have fitting + validation evidence before selection."""
    registry=Path(registry);reg=json.loads(registry.read_text());records=[]
    fitting_ids={};validation_ids={};settings={};data_hashes={}
    for c in reg['candidates']:
        policy_path=registry.parent/c['path'];policy=json.loads(policy_path.read_text())
        if digest(policy_path)!=c['sha256']:raise ValueError('Candidate changed after registration')
        scores={}
        for adapter,runs in c['runs'].items():
            pair={}
            for split in ('fit','validation'):
                m,result=verified_run(Path(run_root)/runs[split],split,adapter,c['sha256'])
                keys=('revision','runner_sha256','legacy_adapter_sha256','max_tokens','concurrency','temperature','threshold','native_cleaning','native_windowing')
                fingerprint={k:m.get(k) for k in keys}
                if adapter in settings and settings[adapter]!=fingerprint:
                    raise ValueError('Adapter/settings changed between candidates')
                settings[adapter]=fingerprint
                if split in data_hashes and data_hashes[split]!=m['dataset_sha256']:
                    raise ValueError('Dataset changed between candidates/models')
                data_hashes[split]=m['dataset_sha256']
                reference=fitting_ids if split=='fit' else validation_ids
                if adapter in reference and reference[adapter]!=m['ids']:
                    raise ValueError('Candidate evaluated on different examples')
                reference[adapter]=m['ids'];pair[split]=result
            scores[adapter]=pair
        records.append(dict(id=policy['id'],sha256=c['sha256'],words=len(' '.join(str(v) for v in policy.values()).split()),scope=c['scope'],scores=scores))
    if len({tuple(v) for v in fitting_ids.values()})!=1 or len({tuple(v) for v in validation_ids.values()})!=1:
        raise ValueError('Models must share fitting and validation examples')
    shared=[r for r in records if r['scope'] in ('initial','shared') and set(r['scores'])==set(POLICY_MODELS)]
    if not shared:raise ValueError('No complete shared candidate')
    ranking=lambda r,adapter=None:(sum(s['validation']['accuracy'] for s in r['scores'].values())/len(r['scores']) if adapter is None else r['scores'][adapter]['validation']['accuracy'],-r['words'],tuple(-ord(x) for x in r['id']))
    winner=max(shared,key=ranking)
    individual={a:max([r for r in records if a in r['scores']],key=lambda r:ranking(r,a))['id'] for a in POLICY_MODELS}
    primary=max(((r['scores'][a]['validation']['accuracy'],-r['words'],a,r['id']) for r in records for a in r['scores']))
    return dict(created_utc=datetime.now(timezone.utc).isoformat(),objective='validation accuracy',
        shared=winner['id'],individual=individual,primary=dict(adapter=primary[2],policy_id=primary[3]),
        records=records,registry_sha256=digest(registry),fitting_ids_sha256=hashlib.sha256(json.dumps(fitting_ids,sort_keys=True).encode()).hexdigest(),
        validation_ids_sha256=hashlib.sha256(json.dumps(validation_ids,sort_keys=True).encode()).hexdigest())


def calibration(selection,registry,run_root,out):
    """Lock score thresholds on validation; never replace the fixed-.5 primary."""
    if Path(out).exists():raise ValueError('Calibration already exists')
    s=json.loads(Path(selection).read_text());reg=json.loads(Path(registry).read_text())
    if s['registry_sha256']!=digest(registry):raise ValueError('Registry changed after selection')
    entries=[]
    for adapter in ('policylm','shieldstral','cope'):
        ids={'wg-p0-taxonomy',s['shared'],s['individual'][adapter]}
        for c in reg['candidates']:
            policy_path=Path(registry).parent/c['path'];policy=json.loads(policy_path.read_text())
            if policy['id'] not in ids:continue
            if digest(policy_path)!=c['sha256']:raise ValueError('Policy mutated')
            path=Path(run_root)/c['runs'][adapter]['validation']
            verified_run(path,'validation',adapter,c['sha256'])
            rows=[json.loads(x) for x in (path/'predictions.jsonl').read_text().split('\n') if x.strip()]
            entries.append(dict(adapter=adapter,policy_id=policy['id'],policy_sha256=c['sha256'],
                validation_run=path.name,predictions_sha256=digest(path/'predictions.jsonl'),
                **calibrate(rows)))
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),selection_sha256=digest(selection),
        role='secondary threshold control; does not change primary policy selection',
        threshold_grid='0.01 through 0.99, step 0.01; ties closest to 0.5, then lower',entries=entries,
        unavailable=['wildguard','safeguard'])
    Path(out).write_text(json.dumps(result,indent=2)+'\n');return result


def freeze(selection,registry,revisions,audit,data_manifest,out,calibration_path=None,final_fit=None):
    if Path(out).exists():raise ValueError('Freeze already exists')
    s=json.loads(Path(selection).read_text());reg=json.loads(Path(registry).read_text())
    if s['registry_sha256']!=digest(registry):raise ValueError('Registry changed after selection')
    model_ids={'policylm':'musubilabs/policylm-1.7b','wildguard':'allenai/wildguard','shieldstral':'mistralai/Shieldstral-1.0-3B','cope':'zentropi-ai/cope-b-a4b','safeguard':'openai/gpt-oss-safeguard-20b'}
    rev=json.loads(Path(revisions).read_text());models={}
    initial=[c for c in reg['candidates'] if c['scope']=='initial']
    if len(initial)!=1:raise ValueError('Exactly one initial policy required')
    initial_id=json.loads((Path(registry).parent/initial[0]['path']).read_text())['id']
    for a,repo in model_ids.items():
        ids=[] if a=='wildguard' else sorted({initial_id,s['shared'],s['individual'][a]})
        hashes=[]
        for policy_id in ids:
            c=next(c for c in reg['candidates'] if json.loads((Path(registry).parent/c['path']).read_text())['id']==policy_id)
            if digest(Path(registry).parent/c['path'])!=c['sha256']:raise ValueError('Policy mutated')
            hashes.append(c['sha256'])
        models[a]=dict(repo=repo,revision=rev[repo]['revision'],policy_ids=ids,policy_hashes=hashes if hashes else [None])
    if {r['split'] for r in read_rows(audit)}!={'audit'}:raise ValueError('Invalid audit data')
    base=Path(__file__).parent
    f=dict(status='frozen',created_utc=datetime.now(timezone.utc).isoformat(),selection_sha256=digest(selection),
        registry_sha256=digest(registry),models=models,primary=s['primary'],
        dataset=rev['dataset'],audit_sha256=digest(audit),data_manifest_sha256=digest(data_manifest),
        runner_sha256=digest(base/'run.py'),metrics_sha256=digest(base/'metrics.py'),legacy_adapter_sha256=digest(base.parent/'run.py'),
        settings=dict(max_tokens=8192,concurrency=32,threshold=.5,temperature=0,reasoning_effort='medium'),
        test_opened=False,policy_editing_closed=True)
    if calibration_path:
        control=json.loads(Path(calibration_path).read_text())
        if control['selection_sha256']!=digest(selection):raise ValueError('Different calibration selection')
        f['calibration_sha256']=digest(calibration_path)
        f['calibration_thresholds']=[dict(adapter=e['adapter'],policy_id=e['policy_id'],policy_sha256=e['policy_sha256'],threshold=e['selected']['threshold']) for e in control['entries']]
    if final_fit:
        rows=read_rows(final_fit)
        if {r['split'] for r in rows}!={'fit'}:raise ValueError('Invalid final fitting population')
        f['final_fit_sha256']=digest(final_fit);f['final_fit_rows']=len(rows)
    Path(out).write_text(json.dumps(f,indent=2)+'\n');return f


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('select');q.add_argument('--registry',required=True);q.add_argument('--runs',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('freeze')
    for name in ('selection','registry','revisions','audit','data-manifest','out'):q.add_argument('--'+name,required=True)
    q.add_argument('--calibration',required=True);q.add_argument('--final-fit',required=True)
    q=sub.add_parser('calibrate')
    for name in ('selection','registry','runs','out'):q.add_argument('--'+name,required=True)
    a=p.parse_args()
    if a.command=='select':
        if Path(a.out).exists():raise ValueError('Selection exists')
        Path(a.out).write_text(json.dumps(select(a.registry,a.runs),indent=2)+'\n')
    elif a.command=='calibrate':calibration(a.selection,a.registry,a.runs,a.out)
    else:freeze(a.selection,a.registry,a.revisions,a.audit,a.data_manifest,a.out,a.calibration,a.final_fit)
