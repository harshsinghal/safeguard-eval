"""Post-hoc, validation-only diagnostics from the frozen public retrieval archive.

No inference, text restoration, test-label access, or configuration selection.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


def audit(archive):
    source_hashes = {}
    checksums = json.loads((archive / 'checksums.json').read_text())

    def read_rows(relative):
        path = archive / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        source_hashes[relative] = digest
        with gzip.open(path, 'rt') as handle:
            return [json.loads(line) for line in handle]

    bank_rows = read_rows('bank-metadata.jsonl.gz')
    bank = {row['id']: row for row in bank_rows}
    metadata = read_rows('metadata/validation.jsonl.gz')
    targets = {row['id']: row for row in metadata}
    retrieval_rows = read_rows('retrieval/validation.jsonl.gz')
    retrieval = {row['id']: row for row in retrieval_rows}
    assert len(bank) == len(bank_rows)
    assert len(targets) == len(metadata)
    assert len(retrieval) == len(retrieval_rows)
    assert targets.keys() == retrieval.keys()
    assert not ({row['group'] for row in bank.values()} &
                {row['group'] for row in targets.values()})
    counts = {}
    for ident, row in retrieval.items():
        neighbors = row['nearest_four']
        assert len(neighbors) == len({x['id'] for x in neighbors}) == 4
        assert row['prompt_sha256'] == targets[ident]['prompt_sha256']
        counts[ident] = sum(bank[x['id']]['expected'] == 'BLOCK' for x in neighbors)

    result = {
        'status': 'post-hoc diagnostic; no new model experiment',
        'split': 'validation',
        'n': len(targets),
        'bank_labels': dict(Counter(row['expected'] for row in bank.values())),
        'retrieval_by_target_label': {},
        'model_conditions': {},
        'conditional_block_counts': {},
    }
    for label in ('ALLOW', 'BLOCK'):
        ids = [i for i, row in targets.items() if row['expected'] == label]
        result['retrieval_by_target_label'][label] = {
            'n': len(ids),
            'nearest_one_same_label': sum(
                bank[retrieval[i]['nearest_four'][0]['id']]['expected'] == label
                for i in ids),
            'nearest_four_harmful_counts': dict(sorted(Counter(counts[i] for i in ids).items())),
        }

    arms = ('policy_only', 'fixed_four', 'nearest_four', 'balanced_nearest')
    for model in ('policylm', 'shieldstral', 'kev', 'jev'):
        rows = read_rows(f'predictions/{model}/validation.jsonl.gz')
        predictions = {(row['id'], row['arm']): row for row in rows}
        assert len(rows) == len(predictions) == len(targets) * len(arms)
        assert set(predictions) == {(ident, arm) for ident in targets for arm in arms}
        for (ident, arm), row in predictions.items():
            assert row['prediction'] in ('ALLOW', 'BLOCK')
            assert row['prompt_sha256'] == targets[ident]['prompt_sha256']
        metrics = {}
        for arm in arms:
            fp = sum(targets[i]['expected'] == 'ALLOW' and
                     predictions[i, arm]['prediction'] == 'BLOCK' for i in targets)
            fn = sum(targets[i]['expected'] == 'BLOCK' and
                     predictions[i, arm]['prediction'] == 'ALLOW' for i in targets)
            metrics[arm] = {'false_blocks': fp, 'misses': fn,
                            'accuracy': (len(targets) - fp - fn) / len(targets)}
        result['model_conditions'][model] = metrics
        buckets = []
        for label in ('ALLOW', 'BLOCK'):
            for count in range(5):
                ids = [i for i, row in targets.items()
                       if row['expected'] == label and counts[i] == count]
                if not ids:
                    continue
                buckets.append({
                    'target_label': label, 'harmful_neighbors': count, 'n': len(ids),
                    'policy_only_blocked': sum(predictions[i, 'policy_only']['prediction'] == 'BLOCK' for i in ids),
                    'nearest_four_blocked': sum(predictions[i, 'nearest_four']['prediction'] == 'BLOCK' for i in ids),
                })
        result['conditional_block_counts'][model] = buckets

    # Check the consumed files against the original immutable manifest.
    recorded = checksums.get('files', checksums)
    for relative, digest in source_hashes.items():
        assert recorded[relative] == digest, f'Archive checksum changed: {relative}'
    result['source_sha256'] = source_hashes
    result['limitations'] = [
        'Descriptive validation analysis chosen after the original study; not a preregistered hypothesis test.',
        'Neighbor label agreement is a diagnostic, not a measure of demonstration usefulness.',
        'Conditional buckets have different prompts; associations do not identify causal mechanisms.',
        'No test labels or source prompt text were read; no new GPU or API calls were made.',
    ]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = json.dumps(audit(args.archive), indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
