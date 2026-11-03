"""Selection, transfer pool, and immutable pre-test choices."""
from pathlib import Path

from evals.policy_transfer.common import (BASE, REGISTRY, check_data, digest, load_run,
    locate, now, read, sources, text_hash, validate_policy, write)


def candidates(state, slug):
    state = Path(state)
    index = read(state / 'candidates.json')
    if index['registry_sha256'] != digest(REGISTRY) or index['sources'] != sources():
        raise ValueError('Candidate registration changed')
    entries = index['candidates'][slug]
    if len(entries) != 4 or len({e['id'] for e in entries}) != 4:
        raise ValueError('Exactly four authored candidates required')
    paths = [BASE]
    for e in entries:
        p = state / e['file']
        if digest(p) != e['sha256'] or text_hash(validate_policy(read(p))) != e['text_sha256']:
            raise ValueError('Candidate text changed')
        paths.append(p)
    return paths


def rank(record):
    return (-record['accuracy'], record['words'], record['id'])


def align(rows, truth):
    if len(rows) != len(truth) or any(any(a[k] != b[k] for k in ('id', 'expected', 'group', 'split'))
                                     for a, b in zip(rows, truth)):
        raise ValueError('Misaligned scored population')


def evaluate(state, slug, policy, split):
    p = read(policy)
    folder = locate(state, slug, p['id'], split)
    rows, summary, _ = load_run(folder, slug, policy, split)
    align(rows, check_data(Path(state) / 'data' / (split + '.jsonl'), split))
    return dict(id=p['id'], file=str(Path(policy).relative_to(state)) if Path(policy) != BASE else 'BASE',
                sha256=digest(policy), text_sha256=text_hash(p),
                words=len(' '.join(p[k] for k in ('purpose', 'block', 'allow', 'precedence')).split()),
                accuracy=summary['accuracy'], summary=summary,
                run=folder.name, predictions_sha256=digest(folder / 'predictions.jsonl'))


def policy_path(state, entry):
    return BASE if entry['file'] == 'BASE' else Path(state) / entry['file']


def select(state):
    state = Path(state)
    reg = read(REGISTRY)
    selected = {}
    searches = {}
    for slug in reg['models']:
        records = []
        for path in candidates(state, slug):
            fit = evaluate(state, slug, path, 'fit')
            val = evaluate(state, slug, path, 'validation')
            records.append(dict(val, fit_accuracy=fit['accuracy'], fit_run=fit['run'],
                                fit_predictions_sha256=fit['predictions_sha256']))
        selected[slug] = min(records, key=rank)
        searches[slug] = records
    # Deduplicate actual text, retaining every source attribution.
    pool = {}
    baseline = dict(id=read(BASE)['id'], file='BASE', sha256=digest(BASE),
                    text_sha256=text_hash(read(BASE)), sources=['baseline'])
    pool[baseline['text_sha256']] = baseline
    for slug, entry in selected.items():
        key = entry['text_sha256']
        if key not in pool:
            pool[key] = {k: entry[k] for k in ('id', 'file', 'sha256', 'text_sha256')}
            pool[key]['sources'] = []
        pool[key]['sources'].append(slug)
    result = dict(created_utc=now(), registry_sha256=digest(REGISTRY), sources=sources(),
                  candidates_sha256=digest(state / 'candidates.json'), selected=selected,
                  searches=searches, pool=list(pool.values()), objective='validation accuracy; ties: fewer policy words, then ID')
    write(state / 'source-selection.json', result)
    return result


def freeze(state):
    state = Path(state)
    selection = read(state / 'source-selection.json')
    if (selection['registry_sha256'] != digest(REGISTRY) or selection['sources'] != sources()
            or selection['candidates_sha256'] != digest(state / 'candidates.json')):
        raise ValueError('Source selection changed')
    # Recompute each source winner, not just trust the stored decision.
    for slug, selected in selection['selected'].items():
        vals = [evaluate(state, slug, p, 'validation') for p in candidates(state, slug)]
        if min(vals, key=rank)['sha256'] != selected['sha256']:
            raise ValueError('Source winner does not reproduce')
    choices = {}
    validation = {}
    for slug in read(REGISTRY)['models']:
        records = [evaluate(state, slug, policy_path(state, e), 'validation') for e in selection['pool']]
        choices[slug] = min(records, key=rank)
        validation[slug] = records
    result = dict(status='frozen', created_utc=now(), sources=sources(),
        registry_sha256=digest(REGISTRY), source_selection_sha256=digest(state / 'source-selection.json'),
        policy_hashes=[e['sha256'] for e in selection['pool']],
        data_hashes=read(REGISTRY)['data_hashes'], recipient_choice=choices, validation=validation,
        primary='WildGuardTest accuracy; all cells retained; no selection on test',
        scope='Exploratory: prior WildGuardTest outcomes were already observed.')
    write(state / 'freeze.json', result)
    return result
