"""Recompute complete recorded results without inference or private prompt text."""
import argparse
import csv
import json
from pathlib import Path
import sys


def analyze(state, out):
    from evals.hatexplain.common import ROOT, REGISTRY, digest, read, rows, run_path, sources, write
    from evals.hatexplain.metrics import paired, report
    from evals.hatexplain.study import candidates, frozen_jobs, load_run
    state, out = Path(state), Path(out)
    reg, frozen = read(REGISTRY), read(state / 'freeze.json')
    if frozen['sources'] != sources() or frozen['registry_sha256'] != digest(REGISTRY):
        raise ValueError('Frozen implementation mismatch')
    if digest(state / 'eligibility.json') != frozen['review_sha256']:
        raise ValueError('Scope reviews changed')
    review = read(state / 'eligibility.json')
    if review['_metadata']['authoring_amendment_sha256'] != digest(state / 'authoring-amendment.json'):
        raise ValueError('Authoring amendment changed')
    amendment = read(state / 'authoring-amendment.json')
    if amendment['repair_source_sha256'] != digest(ROOT / 'docs/hatexplain/editor_repair.py'):
        raise ValueError('Amended editor implementation changed')
    for slug, considered in frozen['considered'].items():
        regenerated = []
        for policy in candidates(state, slug):
            if not review[policy.stem]['eligible']:
                continue
            _, result = load_run(state, slug, policy, 'markdown', 'validation')
            p = read(policy)
            words = sum(len(c['text'].split()) for part in p['sections'].values() for c in part)
            regenerated.append(dict(policy_id=p['id'], macro_f1=result['macro_f1'], accuracy=result['accuracy'], words=words))
        if regenerated != considered:
            raise ValueError('Candidate results changed')
        winner = min(regenerated, key=lambda x: (-x['macro_f1'], -x['accuracy'], x['words'], x['policy_id']))
        if winner['policy_id'] != frozen['selections'][slug]:
            raise ValueError('Selection does not reproduce')
    if frozen_jobs(frozen['selections']) != frozen['jobs']:
        raise ValueError('Final matrix changed')
    verified = []
    for manifest in sorted((state / 'runs').glob('*/manifest.json')):
        m = read(manifest)
        p = state / 'policies' / (m['policy_id'] + '.json')
        data, result = load_run(state, m['slug'], p, m['variant'], m['split'], m['repeat'])
        verified.append(dict(run=manifest.parent.name, n=len(data), errors=result['errors']))
    conditions, predictions = [], {}
    for job in frozen['jobs']:
        slug, identifier, variant, repeat = job['model'], job['policy_id'], job['variant'], job['repeat']
        p = state / 'policies' / (identifier + '.json')
        data, result = load_run(state, slug, p, variant, 'test', repeat)
        predictions[(slug, identifier, variant, repeat)] = data
        conditions.append(dict(job, **result))
    contrasts, repeatability = [], []
    for slug in reg['models']:
        reference = predictions[(slug, 'p0', 'markdown', False)]
        own = predictions[(slug, frozen['selections'][slug], 'markdown', False)]
        for condition in conditions:
            if condition['model'] != slug or condition['repeat']:
                continue
            key = (slug, condition['policy_id'], condition['variant'], False)
            current = predictions[key]
            if key != (slug, 'p0', 'markdown', False):
                contrasts.append(dict(model=slug, policy_id=condition['policy_id'], variant=condition['variant'],
                    reference_policy_id='p0', reference_variant='markdown', **paired(current, reference)))
            if (frozen['selections'][slug] != 'p0' and condition['variant'] == 'markdown'
                    and condition['policy_id'] not in ('p0', frozen['selections'][slug])):
                contrasts.append(dict(model=slug, policy_id=condition['policy_id'], variant='markdown',
                    reference_policy_id=frozen['selections'][slug], reference_variant='markdown', **paired(current, own)))
        repeat = predictions[(slug, 'p0', 'markdown', True)]
        mapping = {r['id']: r for r in reference}
        changes = sum(r['prediction'] != mapping[r['id']]['prediction'] for r in repeat)
        repeatability.append(dict(model=slug, n=len(repeat), changed_decisions=changes,
            initial_accuracy=report([mapping[r['id']] for r in repeat])['accuracy'], repeated_accuracy=report(repeat)['accuracy']))
    result = dict(selections=frozen['selections'], considered=frozen['considered'], conditions=conditions,
                  contrasts=contrasts, repeatability=repeatability, verified_runs=verified,
                  classification_observations=sum(r['n'] for r in verified), errors=sum(r['errors'] for r in verified))
    write(out / 'analysis.json', result)
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'conditions.csv').open('w') as f:
        names = ['model', 'policy_id', 'variant', 'repeat', 'n', 'accuracy', 'macro_f1', 'hate_recall',
                 'missed_hate', 'offensive_false_blocks', 'offensive_n', 'normal_false_blocks', 'normal_n', 'errors']
        writer = csv.DictWriter(f, fieldnames=names); writer.writeheader()
        for c in conditions:
            row = {k: c[k] for k in names if k in c}
            for label in ('offensive', 'normal'):
                part = c['slices']['source_label'][label]
                row[label + '_false_blocks'] = part['false_blocks']; row[label + '_n'] = part['n']
            writer.writerow(row)
    print(json.dumps(dict(verified_runs=len(verified), observations=result['classification_observations'],
                          errors=result['errors'], selections=result['selections'])))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', required=True); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    analyze(args.state, args.out)
