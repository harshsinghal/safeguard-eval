"""Post-hoc validation diagnostics, excluded from configuration selection."""
import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals.retrieval_optimization.common import rows, write, RETRIEVERS
from evals.retrieved_examples.common import vote


def diagnose(state):
    state = Path(state)
    bank = {r['id']: r for r in rows(state / 'bank-short-metadata.jsonl.gz')}
    labels = {r['id']: r['expected'] for r in rows(state / 'metadata/validation.jsonl.gz')}
    result = {'scope': 'post-hoc validation diagnostic, not a selection objective',
              'vote_rule': 'majority of four; nearest neighbor breaks a two-two tie',
              'retrievers': {}}
    for retriever in RETRIEVERS:
        records = rows(state / f'retrieval/{retriever}/validation-short.jsonl.gz')
        if {r['id'] for r in records} != set(labels) or len(records) != len(labels):
            raise ValueError('Incomplete retrieval diagnostic population')
        result['retrievers'][retriever] = {
            'n': len(records),
            'four_neighbor_vote_accuracy': sum(vote(r['rank'][:4], bank) == labels[r['id']]
                                                for r in records) / len(records),
            'nearest_label_agreement': sum(bank[r['rank'][0]['id']]['expected'] == labels[r['id']]
                                          for r in records) / len(records),
        }
    write(state / 'diagnostics/validation-retrieval.json', result)
    path = state / 'predictions/policylm/format-validation.jsonl'
    if not path.exists():
        path = path.with_suffix('.jsonl.gz')
    records = rows(path)
    baseline = {r['id']: r for r in records if r['arm'] == 'policy_only'}
    windows = {}
    for arm in dict.fromkeys(r['arm'] for r in records):
        rr = [r for r in records if r['arm'] == arm]
        windows[arm] = {'n': len(rr), 'window_counts': dict(Counter(r['windows'] for r in rr)),
                        'variant_counts': dict(Counter(r['variants'] for r in rr)),
                        'targets_with_window_count_changed_from_policy_only': sum(
                            r['windows'] != baseline[r['id']]['windows'] for r in rr)}
    write(state / 'diagnostics/policylm-validation-windows.json', {
        'scope': 'post-hoc format-stage diagnostic; counts do not inspect internal activations',
        'conditions': windows})
    print('Wrote validation retrieval and PolicyLM window diagnostics; no selection changed.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True)
    diagnose(**vars(p.parse_args()))
