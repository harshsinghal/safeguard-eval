"""Select on validation, freeze final deployments, and reproduce their metrics."""
import argparse
import json
from pathlib import Path

from evals.frontier_api.run import identity, now, sources
from evals.wildguard.run import digest
from evals.wildguard.metrics import metrics, paired_interval


def load_run(path, registry, arm, policy_hash, split):
    path = Path(path)
    manifest = json.loads((path / 'manifest.json').read_text())
    rows = [json.loads(s) for s in (path / 'predictions.jsonl').read_text().splitlines()]
    expected = dict(arm=arm, identity=identity(registry, arm), sources=sources(),
                    policy_sha256=policy_hash, split=split, dataset_sha256=registry['data_hashes'][split])
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise ValueError('Changed deployment or data: ' + path.name)
    ids = [r['id'] for r in rows]
    if len(rows) != registry['data_counts'][split] or len(set(ids)) != len(ids) or ids != manifest['ids']:
        raise ValueError('Incomplete or duplicated population: ' + path.name)
    if {r['split'] for r in rows} != {split} or any('prompt' in r for r in rows):
        raise ValueError('Wrong split or private text in public predictions')
    summary = json.loads((path / 'summary.json').read_text())
    if not summary.get('complete') or any(summary[k] != v for k, v in metrics(rows).items()):
        raise ValueError('Incomplete run or metric mismatch')
    if digest(path / 'policy.json') != policy_hash:
        raise ValueError('Changed policy artifact')
    return manifest, rows


def select(registry_path, runs):
    registry_path = Path(registry_path)
    r = json.loads(registry_path.read_text())
    records, populations = [], {}
    for c in r['candidates']:
        p = registry_path.parent / c['path']
        if digest(p) != c['sha256']:
            raise ValueError('Changed candidate')
        policy = json.loads(p.read_text())
        scores = {}
        for split in ('fit', 'validation'):
            manifest, rows = load_run(Path(runs) / c['runs'][split], r, c['arm'], c['sha256'], split)
            if split in populations and manifest['ids'] != populations[split]:
                raise ValueError('Different candidate populations')
            populations[split] = manifest['ids']
            scores[split] = metrics(rows)
        records.append(dict(arm=c['arm'], policy_id=policy['id'], policy_sha256=c['sha256'],
            words=len(' '.join(str(v) for v in policy.values()).split()), path=c['path'],
            runs=c['runs'], scores=scores, rationale=c['rationale']))
    selected = {}
    for arm in r['arms']:
        choices = [v for v in records if v['arm'] == arm]
        if len(choices) != r['candidates_per_arm'] or len({v['policy_sha256'] for v in choices}) != len(choices):
            raise ValueError('Expected five distinct candidates per arm')
        if not {'wg-p0-taxonomy', 'wg-p1-concrete-harm', 'wg-p2-boundary-checklist'} <= {v['policy_id'] for v in choices}:
            raise ValueError('Missing shared controls')
        selected[arm] = min(choices, key=lambda v: (-v['scores']['validation']['accuracy'], v['words'], v['policy_id']))['policy_id']
    return dict(created_utc=now(), registry_sha256=digest(registry_path), sources=sources(),
                objective='validation accuracy; shorter text then lexicographic ID', records=records,
                selected=selected, prior_test_results_known=True, exploratory=True)


def freeze(registry_path, selection_path, runs):
    r = json.loads(Path(registry_path).read_text())
    s = json.loads(Path(selection_path).read_text())
    fresh = select(registry_path, runs)
    if any(s.get(k) != fresh[k] for k in ('registry_sha256', 'sources', 'selected', 'records')):
        raise ValueError('Selection is not reproducible from complete candidate runs')
    hashes, ids = {}, {}
    for arm in r['arms']:
        wanted = {'wg-p0-taxonomy', 'wg-p2-boundary-checklist', s['selected'][arm]}
        records = [v for v in s['records'] if v['arm'] == arm and v['policy_id'] in wanted]
        ids[arm] = sorted(wanted)
        hashes[arm] = sorted(v['policy_sha256'] for v in records)
    return dict(status='frozen', created_utc=now(), registry_sha256=digest(registry_path),
        selection_sha256=digest(selection_path), sources=sources(),
        identities={a: identity(r, a) for a in r['arms']}, dataset=r['dataset'], data_hashes=r['data_hashes'],
        final_policy_hashes=hashes, final_policy_ids=ids, selected=s['selected'],
        policy_editing_closed=True, prior_test_results_known=True)


def analyze(registry_path, freeze_path, run_index, runs):
    r = json.loads(Path(registry_path).read_text())
    f = json.loads(Path(freeze_path).read_text())
    if f['registry_sha256'] != digest(registry_path) or f['sources'] != sources():
        raise ValueError('Changed frozen registry or sources')
    index = json.loads(Path(run_index).read_text())
    loaded, result = {}, {}
    expected = {(arm, policy, split) for arm, policies in f['final_policy_ids'].items()
                for policy in policies for split in ('test', 'audit')}
    seen = set()
    for item in index:
        arm, policy, split = item['arm'], item['policy_id'], item['split']
        key = (arm, policy, split)
        if key in seen or key not in expected:
            raise ValueError('Duplicate or unregistered final run')
        seen.add(key)
        candidate = next(c for c in r['candidates'] if c['arm'] == arm and
                         json.loads((Path(registry_path).parent / c['path']).read_text())['id'] == policy)
        manifest, rows = load_run(Path(runs) / item['run'], r, arm, candidate['sha256'], split)
        if manifest['freeze_sha256'] != digest(freeze_path):
            raise ValueError('Wrong freeze')
        loaded[key] = rows
        result[item['run']] = metrics(rows)
    if seen != expected:
        raise ValueError('Missing final populations; never report a partial test as complete')
    comparisons = []
    for model in r['models']:
        low, high = model + '-lower', model + '-higher'
        for policy in ('wg-p0-taxonomy', 'wg-p2-boundary-checklist'):
            comparisons.append(dict(question='reasoning with fixed policy', model=model, policy=policy,
                **paired_interval(loaded[high, policy, 'test'], loaded[low, policy, 'test'])))
        for arm in (low, high):
            comparisons.append(dict(question='selected versus initial policy', arm=arm,
                **paired_interval(loaded[arm, f['selected'][arm], 'test'], loaded[arm, 'wg-p0-taxonomy', 'test'])))
        comparisons.append(dict(question='independently selected deployments; reasoning and prompt may both differ', model=model,
            **paired_interval(loaded[high, f['selected'][high], 'test'], loaded[low, f['selected'][low], 'test'])))
    return dict(metrics=result, comparisons=comparisons, exploratory=True, multiplicity_adjusted=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('select', 'freeze', 'analyze'))
    for name in ('registry', 'runs', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('selection', 'freeze', 'run-index'):
        p.add_argument('--' + name, type=Path)
    args = p.parse_args()
    if args.out.exists():
        raise ValueError('Output exists; do not replace study evidence')
    if args.command == 'select':
        value = select(args.registry, args.runs)
    elif args.command == 'freeze':
        value = freeze(args.registry, args.selection, args.runs)
    else:
        value = analyze(args.registry, args.freeze, args.run_index, args.runs)
    args.out.write_text(json.dumps(value, indent=2) + '\n')
