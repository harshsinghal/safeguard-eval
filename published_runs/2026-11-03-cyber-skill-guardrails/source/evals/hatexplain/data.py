"""Pin the publisher splits; quarantine overlapping development groups without inspecting test errors."""
import argparse
from collections import Counter, defaultdict
import hashlib
from pathlib import Path

from evals.hatexplain.common import SEED, digest, read, write, write_rows
from evals.wildguard.data import group_prompts

HF_REV = 'f6a8b7de6ec31b30919d2f48cf685400ce61185f'
GIT_REV = '01d742279dac941981f53806154481c0e15ee686'
EXPECTED = {'dataset.json': '63bb3340fee0ec469b09690d04cb68f7c187787dd8b83807f071892c084967fb',
            'post_id_divisions.json': 'c2fb0d89862e7897b11ea3e9380753f15a793482b4b70ad0532dfb1212212835'}


def order(row):
    return hashlib.sha256((str(SEED) + row['id']).encode()).hexdigest()


def majority(labels):
    counts = Counter(labels)
    label, count = counts.most_common(1)[0]
    if count <= len(labels) / 2:
        raise ValueError('No majority label')
    return label, count


def stratified(values, n):
    buckets = defaultdict(list)
    for row in values:
        buckets[row['source_label']].append(row)
    quotas = {k: int(n * len(v) / len(values)) for k, v in buckets.items()}
    keys = sorted(buckets, key=lambda k: (-(n * len(buckets[k]) / len(values) - quotas[k]), k))
    for k in keys[:n - sum(quotas.values())]:
        quotas[k] += 1
    return sorted([r for k, v in buckets.items() for r in sorted(v, key=order)[:quotas[k]]], key=lambda r: r['id'])


def prepare(source, state, out):
    source, state, out = Path(source), Path(state), Path(out)
    for name, expected in EXPECTED.items():
        if digest(source / name) != expected:
            raise ValueError('Publisher source changed: ' + name)
    raw, divisions = read(source / 'dataset.json'), read(source / 'post_id_divisions.json')
    seen, all_rows = set(), []
    for original, split in [('train', 'fit'), ('val', 'validation'), ('test', 'test')]:
        for identifier in divisions[original]:
            if identifier in seen:
                raise ValueError('ID overlaps official splits')
            seen.add(identifier)
            post = raw[identifier]
            label, agreement = majority([a['label'] for a in post['annotators']])
            if label not in ('hatespeech', 'normal', 'offensive'):
                raise ValueError('Unexpected label')
            text = ' '.join(post['post_tokens'])
            targets = Counter(t for a in post['annotators'] for t in set(a['target']))
            all_rows.append(dict(id=identifier, prompt=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                expected='BLOCK' if label == 'hatespeech' else 'ALLOW', source_label=label,
                agreement=agreement, targets=sorted(t for t, n in targets.items() if n >= 2),
                split=split, original_split=original, platform='gab' if identifier.endswith('_gab') else 'twitter'))
    grouping = group_prompts(all_rows)
    groups = defaultdict(list)
    for row in all_rows:
        row['group'] = row['group'].replace('wg-', 'hx-', 1)
        groups[row['group']].append(row)
    priority = {'fit': 0, 'validation': 1, 'test': 2}
    excluded, retained = [], []
    for members in groups.values():
        highest = max(priority[r['split']] for r in members)
        for row in members:
            (retained if priority[row['split']] == highest else excluded).append(row)
    train = [r for r in retained if r['split'] == 'fit']
    # Choose training demonstrations before inference. Do not choose them by model success.
    examples = []
    for label, count in [('hatespeech', 2), ('offensive', 1), ('normal', 1)]:
        pool = sorted([r for r in train if r['source_label'] == label and r['agreement'] == 3
                       and 8 <= len(r['prompt'].split()) <= 24], key=order)
        examples += pool[:count]
    if len(examples) != 4:
        raise ValueError('Insufficient demonstration candidates')
    example_groups = {r['group'] for r in examples}
    fit = stratified([r for r in train if r['group'] not in example_groups], 1024)
    selected = dict(fit=fit, validation=sorted([r for r in retained if r['split'] == 'validation'], key=lambda r: r['id']),
                    test=sorted([r for r in retained if r['split'] == 'test'], key=lambda r: r['id']))
    for split, values in selected.items():
        write_rows(state / 'data' / (split + '.jsonl'), values)
    write_rows(state / 'data' / 'repeat.jsonl', stratified(selected['test'], 256))
    write(state / 'training-examples.json', examples)
    # Metadata-only record. Held-out texts and individual labels are not printed during development.
    manifest = dict(hf_repository='Hate-speech-CNERG/hatexplain', hf_revision=HF_REV,
        upstream_repository='hate-alert/HateXplain', upstream_revision=GIT_REV,
        source_hashes={name: digest(source / name) for name in EXPECTED},
        original_counts={k: len(v) for k, v in divisions.items()}, grouping=grouping,
        quarantine_rule='Keep highest-priority split in each duplicate component: test > validation > train; never remove test rows.',
        excluded=[{k: r[k] for k in ('id', 'split', 'group')} for r in excluded],
        unused_source_rows=len(raw) - len(seen),
        text_reconstruction='Join publisher post_tokens with one ASCII space; no other text rewriting.',
        label_mapping={'hatespeech': 'BLOCK', 'offensive': 'ALLOW', 'normal': 'ALLOW'},
        selection_seed=SEED, fit_selection='Proportional majority-label strata; deterministic SHA256 ordering; demonstration groups excluded.',
        counts={k: len(v) for k, v in selected.items()},
        data_hashes={k: digest(state / 'data' / (k + '.jsonl')) for k in (*selected, 'repeat')},
        example_ids=[r['id'] for r in examples],
        example_selection='First unanimous training rows by seeded hash within 8–24 tokens: two hate, one offensive, one normal.',
        contamination_limit='Upstream model exposure to this public benchmark is unknown; deduplication is approximate, not semantic.')
    write(out / 'data-manifest.json', manifest)
    print({'counts': manifest['counts'], 'quarantined': len(excluded), 'groups': grouping['groups'],
           'example_ids': manifest['example_ids']})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True); p.add_argument('--state', required=True); p.add_argument('--out', required=True)
    prepare(**vars(p.parse_args()))
