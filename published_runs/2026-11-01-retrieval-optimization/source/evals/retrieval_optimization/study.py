import argparse
from collections import defaultdict
import shutil
from .common import *
from evals.retrieved_examples.report import metrics, delta


def prepare(state, prior):
    state, prior = Path(state), Path(prior)
    if state.exists():
        raise ValueError('Use a fresh study directory')
    old = read(prior / 'registration.json')
    hashes = {}
    for rel, expected in old['hashes'].items():
        if digest(prior / rel) != expected:
            raise ValueError('Prior registered data changed: ' + rel)
    for rel in ('inputs', 'metadata', 'policies'):
        shutil.copytree(prior / rel, state / rel)
    populations = [rows(state / f'metadata/{s}.jsonl.gz') for s in ('fit', 'validation', 'test')]
    assert_disjoint(*populations)
    if [len(x) for x in populations] != [4096, 1536, 1699]:
        raise ValueError('Unexpected population')
    fit = rows(state / 'inputs/fit.jsonl')
    if [x['id'] for x in fit] != [x['id'] for x in populations[0]]:
        raise ValueError('Misaligned fitting data')
    fit = [{**x, **m} for x, m in zip(fit, populations[0])]
    groups = defaultdict(list)
    for r in fit:
        groups[r['group']].append(r)
    expanded = []
    for group, members in sorted(groups.items()):
        if len({r['expected'] for r in members}) != 1:
            continue
        eligible = [r for r in members if r['prompt'].strip() and 8 <= len(r['prompt'].split()) <= 160 and len(r['prompt']) <= 800]
        if eligible:
            expanded.append(min(eligible, key=lambda r: r['id']))
    short = rows(prior / 'private-bank.jsonl')
    # Preserve each original representative when the expanded group has others.
    short_groups = {r['group']: r for r in short}
    expanded = sorted([short_groups.get(r['group'], r) for r in expanded], key=lambda r: r['id'])
    for name, bank in (('short', short), ('expanded', expanded)):
        write_rows(state / f'private-bank-{name}.jsonl', bank)
        write_rows(state / f'bank-{name}-metadata.jsonl.gz', [{k: v for k, v in r.items() if k != 'prompt'} for r in bank])
    if not {r['id'] for r in short} <= {r['id'] for r in expanded}:
        raise ValueError('Expanded bank must contain original representatives')
    cache = state / 'private-e5-cache'
    cache.mkdir()
    for name in ('bank.npy', 'smoke.npy', 'validation.npy'):
        shutil.copy2(prior / 'private-embeddings' / name, cache / name)
    for model in MODELS:
        for split in ('smoke', 'validation'):
            path = prior / f'predictions/{model}/{split}.jsonl'
            if not path.exists():
                path = path.with_suffix('.jsonl.gz')
            write_rows(state / f'cache/{model}/{split}.jsonl.gz', rows(path))
    smoke_groups = {r['group'] for r in rows(state / 'metadata/smoke.jsonl.gz')}
    fixed_sets = {str(i): fixed(short, i, old['fixed_ids']) for i in range(3)}
    for ids in fixed_sets.values():
        if any(r['group'] in smoke_groups for r in short if r['id'] in ids):
            # Smoke fixed controls are not used for selection; nevertheless keep them disjoint.
            raise ValueError('Fixed set overlaps original smoke; amend sample before inference')
    for path in sorted(state.rglob('*')):
        if path.is_file():
            hashes[str(path.relative_to(state))] = digest(path)
    audit = []
    short_ids = {r['id'] for r in short}
    for eligible in (True, False):
        for label in ('ALLOW', 'BLOCK'):
            rr = sorted([r for r in fit if (r['id'] in short_ids) == eligible and r['expected'] == label],
                        key=lambda r: hashlib.sha256(('retrieval-opt-audit:' + r['id']).encode()).hexdigest())[:6]
            audit += [{'id': r['id'], 'eligible': eligible, 'expected': label, 'words': len(r['prompt'].split()),
                       'characters': len(r['prompt']), 'prompt_sha256': r['prompt_sha256']} for r in rr]
    write(state / 'bank-audit.json', {'sample': audit, 'short_n': len(short), 'expanded_n': len(expanded),
          'short_labels': dict(Counter(r['expected'] for r in short)),
          'expanded_labels': dict(Counter(r['expected'] for r in expanded)),
          'labels_changed': 0, 'sample_rule': 'six per eligibility/label cell; SHA256 retrieval-opt-audit:ID'})
    hashes['bank-audit.json'] = digest(state / 'bank-audit.json')
    write(state / 'registration.json', {'created_utc': now(), 'sources': sources(), 'hashes': hashes,
          'models': MODELS, 'encoders': ENCODERS, 'reranker': RERANKER, 'retrieval_instruction': INSTRUCTION,
          'rerank_instruction': RERANK_INSTRUCTION, 'fixed_sets': fixed_sets,
          'prior_registration_sha256': digest(prior / 'registration.json'),
          'prior_retrieval_cost_usd': .874933148, 'shared_cap_usd': 20, 'new_max_usd': 19.125066852,
          'populations': {s: len(m) for s, m in zip(('fit', 'validation', 'test'), populations)},
          'decision_rules': 'unchanged: PolicyLM/Shieldstral >=0.5; Kev/Jev native Choice argmax',
          'test_status': 'reused public benchmark; exploratory'}, exclusive=True)
    print(canonical({'short_n': len(short), 'expanded_n': len(expanded), 'fixed_sets': fixed_sets}))


def configurations(state, stage):
    if stage == 'format':
        return {m: {config_id(c): c for c in [config(method='none')] +
                [config(style, method=method) for style in ('original', 'native') for method in ('nearest4', 'balanced4')]}
                for m in MODELS}
    formats = read(state / 'selection-format.json')['selected']
    if stage == 'retriever':
        return {m: {config_id(c): c for c in [config(formats[m], r) for r in RETRIEVERS]} for m in MODELS}
    winners = read(state / 'selection-retriever.json')['selected']
    if stage == 'selector':
        return {m: {config_id(c): c for c in [config(formats[m], winners[m]['retriever'], method)
                for method in METHODS] + [config(formats[m], 'e5', f'fixed{i}') for i in range(3)]}
                for m in MODELS}
    if stage == 'coverage':
        return {m: {config_id(c): c for c in [config(formats[m], winners[m]['retriever'], 'nearest2', bank)
                for bank in ('short', 'expanded')]} for m in MODELS}
    if stage == 'test':
        return read(state / 'freeze.json')['configurations']
    raise ValueError(stage)


def jobs(state, stage, split):
    state = Path(state)
    reg = verify(state, test=split == 'test')
    if (split == 'test') != (stage == 'test'):
        raise ValueError('Test jobs require the final frozen stage')
    cfgs = configurations(state, stage)
    query = rows(state / f'inputs/{split}.jsonl')
    banks = {k: rows(state / f'private-bank-{k}.jsonl') for k in ('short', 'expanded')}
    lookup = {k: {r['id']: r for r in rr} for k, rr in banks.items()}
    rr_cache, rk_cache, vec_cache = {}, {}, {}
    manifest = {'stage': stage, 'split': split, 'configurations': cfgs, 'jobs': {}, 'n': len(query), 'created_utc': now()}
    for model, cc in cfgs.items():
        out = []
        base = read(state / f'policies/{model}.json')
        for cid, c in cc.items():
            method = c['method']
            key = (c['retriever'], c['bank'])
            if method != 'none' and not method.startswith('fixed') and key not in rr_cache:
                path = state / f'retrieval/{key[0]}/{split}-{key[1]}.jsonl.gz'
                if digest(path) != read(path.with_suffix('.manifest.json'))['sha256']:
                    raise ValueError('Changed retrieval')
                rr_cache[key] = {r['id']: r for r in rows(path)}
            if method in ('rerank2', 'rerank4', 'contrast4', 'gated2') and c['retriever'] not in rk_cache:
                path = state / f'rerank/{c["retriever"]}/{split}.jsonl.gz'
                if digest(path) != read(path.with_suffix('.manifest.json'))['sha256']:
                    raise ValueError('Changed reranking')
                rk_cache[c['retriever']] = {r['id']: r['candidates'] for r in rows(path)}
            vectors = None
            if method == 'mmr4' and c['retriever'] != 'bm25':
                if c['retriever'] not in vec_cache:
                    from .features import checked_array
                    v = checked_array(state / f'private-embeddings/{c["retriever"]}/bank.npy')
                    vec_cache[c['retriever']] = {r['id']: a for r, a in zip(banks['expanded'], v)}
                vectors = vec_cache[c['retriever']]
            threshold = read(state / f'retrieval/{c["retriever"]}/gate.json')['threshold'] if method == 'gated2' else 0
            for q in query:
                if set(q) != {'id', 'prompt', 'prompt_sha256'} or hashlib.sha256(q['prompt'].encode()).hexdigest() != q['prompt_sha256']:
                    raise ValueError('Query must be label-free with matching content')
                if method == 'none':
                    ids = []
                elif method.startswith('fixed'):
                    ids = reg['fixed_sets'][method[-1]]
                else:
                    rr = rr_cache[key][q['id']]
                    if rr['prompt_sha256'] != q['prompt_sha256']:
                        raise ValueError('Neighbor/target mismatch')
                    ids = choose(c, rr, lookup[c['bank']], threshold, vectors, rk_cache.get(c['retriever'], {}).get(q['id']))
                if len(ids) != len(set(ids)) or len(ids) not in (0, 2, 4):
                    raise ValueError('Wrong example count')
                body = {'content': q['prompt'], 'policy': render(base, model, [lookup[c['bank']][i] for i in ids], c['format'])}
                out.append({'id': q['id'], 'arm': cid, 'example_ids': ids, 'prompt_sha256': q['prompt_sha256'],
                            'request_sha256': hash_value(body), 'body': body})
        dest = state / f'jobs/{model}/{stage}-{split}.jsonl.gz'
        if dest.exists():
            if rows(dest) != out:
                raise ValueError('Existing jobs differ')
        else:
            write_rows(dest, out)
        manifest['jobs'][model] = digest(dest)
    path = state / f'jobs/{stage}-{split}-manifest.json'
    if path.exists():
        previous = read(path)
        if previous['jobs'] != manifest['jobs'] or previous['configurations'] != cfgs:
            raise ValueError('Existing job manifest differs')
    else:
        write(path, manifest, exclusive=True)
    print(canonical({'stage': stage, 'split': split, 'n': len(query), 'configurations_per_model': {m: len(c) for m, c in cfgs.items()}}))


def aligned(state, model, stage, split):
    state = Path(state)
    meta = rows(state / f'metadata/{split}.jsonl.gz')
    manifest = read(state / f'jobs/{stage}-{split}-manifest.json')
    cfgs = manifest['configurations'][model]
    rr = rows(state / f'predictions/{model}/{stage}-{split}.jsonl')
    by = {(r['id'], r['arm']): r for r in rr}
    if len(by) != len(rr) or set(by) != {(r['id'], c) for r in meta for c in cfgs}:
        raise ValueError('Incomplete or duplicate predictions')
    predictions, mm = {}, {}
    for cid in cfgs:
        pp = []
        counts = []
        for m in meta:
            r = by[m['id'], cid]
            if r['prompt_sha256'] != m['prompt_sha256'] or r['prediction'] not in ('ALLOW', 'BLOCK'):
                raise ValueError('Invalid prediction identity')
            pp.append(int(r['prediction'] == 'BLOCK'))
            counts.append(len(r['example_ids']))
        predictions[cid] = np.array(pp)
        mm[cid] = {**metrics(meta, predictions[cid]), 'mean_examples': float(np.mean(counts))}
    return meta, predictions, mm


def select(state, stage):
    state = Path(state)
    verify(state)
    cfgs = configurations(state, stage)
    selected, table, hashes = {}, {}, {}
    for model in MODELS:
        _, _, mm = aligned(state, model, stage, 'validation')
        table[model] = mm
        path = f'predictions/{model}/{stage}-validation.jsonl'
        hashes[path] = digest(state / path)
        if stage == 'format':
            def rank(style):
                vv = [mm[config_id(config(style, method=k))] for k in ('nearest4', 'balanced4')]
                return (-sum(x['accuracy'] for x in vv), -sum(x['balanced_accuracy'] for x in vv), style != 'original')
            selected[model] = min(('original', 'native'), key=rank)
        elif stage == 'retriever':
            best = min(cfgs[model], key=lambda c: (-mm[c]['accuracy'], -mm[c]['balanced_accuracy'], RETRIEVERS.index(cfgs[model][c]['retriever'])))
            selected[model] = cfgs[model][best]
        else:
            raise ValueError(stage)
    write(state / f'selection-{stage}.json', {'created_utc': now(), 'selected': selected, 'validation': table,
          'hashes': hashes, 'registration_sha256': digest(state / 'registration.json')}, exclusive=True)
    print(canonical(selected))


def freeze(state):
    state = Path(state)
    verify(state)
    tables, configs, roles, hashes = {}, {}, {}, {}
    formats = read(state / 'selection-format.json')['selected']
    retrievers = read(state / 'selection-retriever.json')['selected']
    for model in MODELS:
        mm, cc = {}, {}
        for stage in ('format', 'retriever', 'selector', 'coverage'):
            _, _, values = aligned(state, model, stage, 'validation')
            for cid, value in values.items():
                if cid in mm and mm[cid] != value:
                    raise ValueError('Repeated configuration metrics differ')
                mm[cid] = value
            cc.update(configurations(state, stage)[model])
        key = lambda cid: (-mm[cid]['accuracy'], -mm[cid]['balanced_accuracy'], mm[cid]['mean_examples'], cid)
        best = min(cc, key=key)
        retrieval = min((c for c in cc if cc[c]['method'] != 'none' and not cc[c]['method'].startswith('fixed')), key=key)
        selected_roles = {'policy_only': 'policy_only', 'original_nearest': config_id(config()),
            'format_selected': config_id(config(formats[model])),
            'retriever_selected': config_id(retrievers[model]), 'retrieval_selected': retrieval, 'system_selected': best}
        roles[model] = selected_roles
        configs[model] = {cid: cc[cid] for cid in dict.fromkeys(selected_roles.values())}
        tables[model] = mm
    for pattern in ('selection-*.json', 'predictions/*/*-validation.jsonl', 'jobs/*-validation-manifest.json', 'retrieval/*/gate.json'):
        for p in state.glob(pattern):
            hashes[str(p.relative_to(state))] = digest(p)
    write(state / 'freeze.json', {'created_utc': now(), 'roles': roles, 'configurations': configs,
          'validation': tables, 'hashes': hashes, 'registration_sha256': digest(state / 'registration.json')}, exclusive=True)
    print(canonical(roles))


def evaluate(state):
    state = Path(state)
    verify(state, test=True)
    f = read(state / 'freeze.json')
    table, contrasts, stages = {}, {}, {}
    for model in MODELS:
        meta, pp, mm = aligned(state, model, 'test', 'test')
        table[model] = mm
        roles = f['roles'][model]
        pairs = [('policy_only', 'system_selected'), ('policy_only', 'retrieval_selected'),
                 ('original_nearest', 'format_selected'), ('format_selected', 'retriever_selected'),
                 ('retriever_selected', 'retrieval_selected'), ('original_nearest', 'retrieval_selected')]
        contrasts[model] = {a + ' -> ' + b: delta(meta, pp[roles[a]], pp[roles[b]]) for a, b in pairs}
        stages[model] = {s: aligned(state, model, s, 'validation')[2] for s in ('format', 'retriever', 'selector', 'coverage')}
    result = {'created_utc': now(), 'roles': f['roles'], 'configurations': f['configurations'], 'test': table,
              'validation': f['validation'], 'stages': stages, 'paired': contrasts,
              'scope': 'Fixed model weights/decisions; staged validation selection; reused public test, exploratory'}
    write(state / 'results.json', result)
    lines = ['# Retrieval optimization results', '',
             'Frozen validation selections on 1,699 reused WildGuardTest prompts; no output calibration.', '',
             '| Model | Role | Accuracy | Balanced accuracy | False blocks | Misses | Mean examples |',
             '|---|---|---:|---:|---:|---:|---:|']
    for model, roles in f['roles'].items():
        for role, cid in roles.items():
            x = table[model][cid]
            lines.append(f"| {model} | {role} | {x['accuracy']:.2%} | {x['balanced_accuracy']:.2%} | {x['false_blocks']} | {x['misses']} | {x['mean_examples']:.2f} |")
    lines += ['', 'Roles that map to the same configuration reuse identical predictions; they are not independent trials.', '',
              '## Paired accuracy changes', '', '| Model | Contrast | Change (pp) | 95% interval (pp) | Corrected | Introduced |',
              '|---|---|---:|---|---:|---:|']
    for model, cc in contrasts.items():
        for name, c in cc.items():
            lines.append(f"| {model} | {name} | {100*c['accuracy_difference']:+.2f} | {100*c['ci95'][0]:+.2f} to {100*c['ci95'][1]:+.2f} | {c['corrected']} | {c['introduced']} |")
    lines += ['', 'Intervals are descriptive, unadjusted paired group bootstraps. Test reuse and validation search limit generalization.', '',
              '## All validation configurations', '', '| Model | Configuration | Accuracy | Balanced accuracy | False blocks | Misses |',
              '|---|---|---:|---:|---:|---:|']
    for model, mm in f['validation'].items():
        for cid, x in mm.items():
            lines.append(f"| {model} | {cid} | {x['accuracy']:.2%} | {x['balanced_accuracy']:.2%} | {x['false_blocks']} | {x['misses']} |")
    (state / 'RESULTS.md').write_text('\n'.join(lines) + '\n')
    print(canonical({m: {r: table[m][c]['accuracy'] for r, c in rr.items()} for m, rr in f['roles'].items()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'jobs', 'select', 'freeze', 'evaluate'])
    p.add_argument('--state', required=True)
    p.add_argument('--prior')
    p.add_argument('--stage', choices=['format', 'retriever', 'selector', 'coverage', 'test'])
    p.add_argument('--split', choices=['smoke', 'validation', 'test'], default='validation')
    a = p.parse_args()
    if a.action == 'prepare': prepare(a.state, a.prior)
    elif a.action == 'jobs': jobs(a.state, a.stage, a.split)
    elif a.action == 'select': select(a.state, a.stage)
    elif a.action == 'freeze': freeze(a.state)
    else: evaluate(a.state)
