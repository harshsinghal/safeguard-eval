"""Prepare training partitions without fetching or reading WildGuardTest."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

SEED = 20261024
REVISION = 'd29c47f41c8b51348b5c8e8c81c039b3132b66d1'


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def shingles(text):
    words = re.findall(r'\w+', normalized(text))
    return {' '.join(words[i:i+5]) for i in range(len(words)-4)} or {normalized(text)}


def group_prompts(rows):
    from datasketch import MinHash, MinHashLSH
    exact, members = {}, defaultdict(list)
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        a, b = root(i), root(j)
        parent[max(a, b)] = min(a, b)
    index = MinHashLSH(threshold=.65, num_perm=64)
    sets = {}
    near_pairs = []
    for i, row in enumerate(rows):
        key = normalized(row['prompt'])
        if key in exact:
            union(i, exact[key])
            continue
        exact[key] = i
        s = shingles(key)
        h = MinHash(num_perm=64, seed=SEED)
        h.update_batch([x.encode() for x in sorted(s)])
        for other in index.query(h):
            j = int(other)
            similarity = len(s & sets[j]) / len(s | sets[j])
            if similarity >= .85:
                union(i, j)
                near_pairs.append((rows[i]['id'], rows[j]['id'], similarity))
        sets[i] = s
        index.insert(str(i), h)
        if i and i % 10000 == 0:
            print(f'Grouping training row {i}', flush=True)
    for i, row in enumerate(rows):
        members[root(i)].append(row)
    for values in members.values():
        group = 'wg-' + min(sha(normalized(r['prompt'])) for r in values)[:20]
        for row in values:
            row['group'] = group
    return dict(unique_normalized_prompts=len(exact), groups=len(members),
                near_duplicate_pairs=len(near_pairs),
                conflicting_label_groups=sum(len({r['expected'] for r in v}) > 1 for v in members.values()),
                grouping='NFKC/casefold/whitespace exact; 64-permutation 5-word MinHash LSH candidates at 0.65, verified Jaccard >=0.85; connected components',
                limitation='Approximate candidate retrieval may miss some near duplicates; no semantic paraphrase detector.')


def stratum(row):
    return (row['expected'], str(row['adversarial']), row['subcategory'])


def split_groups(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['group']].append(row)
    buckets = defaultdict(list)
    for group, values in grouped.items():
        bucket = sorted(Counter(stratum(r) for r in values).items(), key=lambda x: (-x[1], x[0]))[0][0]
        buckets[bucket].append((group, values))
    ratios = {'fit': .8, 'validation': .1, 'audit': .1}
    for bucket, groups in sorted(buckets.items()):
        groups.sort(key=lambda item: sha(str(SEED) + item[0]))
        total = sum(len(v) for _, v in groups)
        assigned = Counter()
        for _, values in groups:
            # Largest normalized remaining quota; ties favor fit.
            split = max(ratios, key=lambda s: (total * ratios[s] - assigned[s]) / ratios[s])
            assigned[split] += len(values)
            for row in values:
                row['split'] = split
    return rows


def sample(rows, n, seed=SEED):
    """Proportional stratified sample, stable under source row reordering."""
    if n >= len(rows):
        return sorted(rows, key=lambda r: r['id'])
    buckets = defaultdict(list)
    for row in rows:
        buckets[stratum(row)].append(row)
    quotas = {s: int(n * len(v) / len(rows)) for s, v in buckets.items()}
    remaining = n - sum(quotas.values())
    order = sorted(buckets, key=lambda s: (-(n*len(buckets[s])/len(rows)-quotas[s]), s))
    for s in order[:remaining]:
        quotas[s] += 1
    selected = []
    for s, values in sorted(buckets.items()):
        selected.extend(sorted(values, key=lambda r: sha(str(seed)+r['id']))[:quotas[s]])
    return sorted(selected, key=lambda r: r['id'])


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))


def prepare(source, out):
    import pyarrow.parquet as pq
    out.mkdir(parents=True, exist_ok=False)
    raw = pq.read_table(source).to_pylist()
    rows = []
    for i, r in enumerate(raw):
        label = r['prompt_harm_label']
        if label is None:
            continue
        if label not in ('harmful', 'unharmful') or not isinstance(r['prompt'], str):
            raise ValueError(f'Invalid source row {i}')
        rows.append(dict(id=f'wgtrain-{i:06}', source_index=i, prompt=r['prompt'],
            prompt_sha256=sha(r['prompt']), expected='BLOCK' if label=='harmful' else 'ALLOW',
            adversarial=r.get('adversarial'), subcategory=r.get('subcategory') or 'unspecified'))
    grouping = group_prompts(rows)
    split_groups(rows)
    counts = {s:dict(n=sum(r['split']==s for r in rows),
        labels=dict(Counter(r['expected'] for r in rows if r['split']==s)),
        strata=dict(Counter('|'.join(stratum(r)) for r in rows if r['split']==s)))
        for s in ('fit','validation','audit')}
    write_jsonl(out/'train.jsonl', rows)
    write_jsonl(out/'assignments.jsonl', [{k:v for k,v in r.items() if k!='prompt'} for r in rows])
    samples = {}
    for name, split, n in [('pilot','fit',256),('fit-search','fit',1024),('validation-search','validation',512),('audit-budget','audit',512)]:
        chosen = sample([r for r in rows if r['split']==split], n)
        write_jsonl(out/(name+'.jsonl'), chosen)
        samples[name] = dict(n=len(chosen), split=split, ids_sha256=sha('\n'.join(r['id'] for r in chosen)))
    manifest = dict(dataset='allenai/wildguardmix', revision=REVISION, config='wildguardtrain', seed=SEED,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), source_rows=len(raw),
        included_rows=len(rows), excluded_null_labels=len(raw)-len(rows), grouping=grouping,
        splits=counts,samples=samples, test_accessed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='splits'},indent=2))
    print(json.dumps({s:{k:v for k,v in v.items() if k!='strata'} for s,v in counts.items()},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();prepare(a.source,a.out)
