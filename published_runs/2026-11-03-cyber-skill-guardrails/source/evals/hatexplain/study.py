"""Review gates, validation selection, and prospective final-run freeze."""
import argparse
import hashlib
import json
from pathlib import Path

from evals.hatexplain.common import ROOT, REGISTRY, digest, now, read, rows, run_path, sources, write
from evals.hatexplain.metrics import report
from evals.hatexplain.policy import OMISSIONS, validate


def candidates(state, slug):
    folder = Path(state) / 'policies'
    return [folder / (identifier + '.json') for identifier in ('p0', slug + '-p1', slug + '-p2')
            if (folder / (identifier + '.json')).exists()]


def load_run(state, slug, policy, variant, split, repeat=False):
    path = run_path(state, slug, read(policy)['id'], variant, split, repeat)
    m, result = read(path / 'manifest.json'), read(path / 'summary.json')
    data = rows(path / 'predictions.jsonl')
    reg = read(REGISTRY)
    if (m['sources'] != sources() or m['registry_sha256'] != digest(REGISTRY)
            or m['policy_sha256'] != digest(policy) or m['variant'] != variant
            or m['dataset_sha256'] != reg['data_hashes']['repeat' if repeat else split]
            or m['revision'] != reg['models'][slug]['revision'] or m['settings'] != reg['settings']
            or [r['id'] for r in data] != m['ids'] or not result['complete']):
        raise ValueError('Recorded run identity mismatch: ' + str(path))
    recomputed = report(data)
    if any(recomputed[k] != result[k] for k in recomputed):
        raise ValueError('Metrics do not reproduce')
    return data, result


def frozen_jobs(selections):
    jobs = []
    for slug in read(REGISTRY)['models']:
        variants = ['markdown', *OMISSIONS]
        if slug != 'policylm':
            variants += ['linear', 'tagged', 'reordered']
        for variant in variants:
            jobs.append(dict(model=slug, policy_id='p0', variant=variant, repeat=False))
        for identifier in sorted(set(selections.values()) - {'p0'}):
            jobs.append(dict(model=slug, policy_id=identifier, variant='markdown', repeat=False))
        jobs.append(dict(model=slug, policy_id='p0', variant='markdown', repeat=True))
    return jobs


def freeze(state):
    state = Path(state); reg = read(REGISTRY)
    review = read(state / 'eligibility.json')
    choices, considered = {}, {}
    for slug in reg['models']:
        entries = []
        for policy in candidates(state, slug):
            p = validate(read(policy)); identifier = p['id']
            if review[identifier]['policy_sha256'] != digest(policy):
                raise ValueError('Scope review does not match policy')
            if not review[identifier]['eligible']:
                continue
            _, result = load_run(state, slug, policy, 'markdown', 'validation')
            words = sum(len(c['text'].split()) for part in p['sections'].values() for c in part)
            entries.append(dict(policy_id=identifier, macro_f1=result['macro_f1'], accuracy=result['accuracy'], words=words))
        if not entries:
            raise ValueError('No eligible candidate')
        chosen = min(entries, key=lambda x: (-x['macro_f1'], -x['accuracy'], x['words'], x['policy_id']))
        choices[slug] = chosen['policy_id']; considered[slug] = entries
    policies = {p.stem: digest(p) for p in sorted((state / 'policies').glob('*.json'))}
    frozen = dict(status='frozen', created_utc=now(), sources=sources(), registry_sha256=digest(REGISTRY),
        protocol_sha256=digest(ROOT / 'docs/hatexplain/PLAN.md'), review_sha256=digest(state / 'eligibility.json'),
        selections=choices, considered=considered, policy_hashes=policies, jobs=frozen_jobs(choices),
        data_hashes=reg['data_hashes'])
    write(state / 'freeze.json', frozen)
    print(json.dumps(dict(selections=choices, final_jobs=len(frozen['jobs']), freeze_sha256=digest(state / 'freeze.json'))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--state', required=True)
    freeze(**vars(p.parse_args()))
