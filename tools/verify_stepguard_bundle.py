"""Audit published StepGuard counts and hashes without data downloads or inference."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_metrics(records, reported):
    counts = Counter((r['expected'], r['prediction']) for r in records)
    assert all(g in ('ALLOW', 'BLOCK') and p in ('ALLOW', 'BLOCK', 'ERROR')
               for g, p in counts)
    tn = counts['ALLOW', 'ALLOW']
    tp = counts['BLOCK', 'BLOCK']
    fp = counts['ALLOW', 'BLOCK']
    fn = counts['BLOCK', 'ALLOW']
    en = counts['ALLOW', 'ERROR']
    ep = counts['BLOCK', 'ERROR']
    neg, pos, n = tn + fp + en, tp + fn + ep, len(records)
    expected = dict(n=n, positives=pos, negatives=neg, false_blocks=fp,
                    missed_violations=fn, unresolved=en + ep,
                    accuracy=(tn + tp) / n, coverage=1 - (en + ep) / n,
                    recall=tp / pos if pos else None,
                    specificity=tn / neg if neg else None,
                    false_positive_rate=fp / neg if neg else None,
                    false_negative_rate=fn / pos if pos else None,
                    balanced_accuracy=(tp / pos + tn / neg) / 2 if pos and neg else None)
    assert reported['confusion'] == dict(tp=tp, tn=tn, fp=fp, fn=fn,
                                         error_allow=en, error_block=ep)
    for key, value in expected.items():
        actual = reported[key]
        assert (actual is None if value is None else
                actual is not None and math.isclose(actual, value, abs_tol=1e-12)), key


def main(bundle):
    root = Path(bundle).resolve()
    manifest = read(root / 'published-manifest.json')
    for rel, expected in manifest['files'].items():
        path = (root / rel).resolve()
        assert root in path.parents and path.is_file(), rel
        assert checksum(path) == expected, rel
    actual_files = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert actual_files == set(manifest['files']) | {'published-manifest.json'}
    selection = read(root / 'selection.json')['models']
    eligibility = read(root / 'eligibility.json')
    results = read(root / 'results.json')
    assert results['registration_sha256'] == checksum(root / 'registration.json')
    assert results['freeze_sha256'] == checksum(root / 'freeze.json')
    # Public frozen files must still match. Private inputs can be restored separately.
    for filename in ('registration.json', 'freeze.json'):
        for rel, expected in read(root / filename)['files'].items():
            if (root / rel).exists():
                assert checksum(root / rel) == expected, rel

    predictions_checked = 0
    for model, tasks in selection.items():
        allowed = set(eligibility['policylm' if model == 'policylm' else 'primary'])
        for task, chosen in tasks.items():
            population = {r['id']: r for r in rows(root / f'metadata/{task}/validation.jsonl')
                          if r['id'] in allowed}
            for candidate, evidence in chosen['candidates'].items():
                records = rows(root / f'predictions/{model}/{task}/validation/{candidate}.jsonl')
                assert len(records) == len(population) == len({r['id'] for r in records})
                for record in records:
                    original = population[record['id']]
                    assert all(record[k] == original[k] for k in original)
                audit_metrics(records, evidence['metrics'])
                predictions_checked += len(records)
            ordered = sorted(chosen['candidates'], key=lambda pid: (
                -chosen['candidates'][pid]['metrics']['balanced_accuracy'],
                chosen['candidates'][pid]['tie_length'], pid))
            assert chosen['selected'] == ordered[0], (model, task)

    panels_checked = 0
    for task, cohorts in results['results'].items():
        for cohort, panel in cohorts.items():
            allowed = set(eligibility['policylm' if cohort == 'short' else 'primary'])
            population = {r['id']: r for r in rows(root / f'metadata/{task}/test.jsonl')
                          if r['id'] in allowed}
            assert len(population) == panel['n']
            assert dict(Counter(r['expected'] for r in population.values())) == panel['classes']
            for model, arms in panel['models'].items():
                for arm in ('initial', 'selected'):
                    expected_policy = 'initial' if arm == 'initial' else selection[model][task]['selected']
                    assert arms[arm]['policy'] == expected_policy
                    records = [r for r in rows(root / f'predictions/{model}/{task}/test/{expected_policy}.jsonl')
                               if r['id'] in population]
                    assert len(records) == len(population) == len({r['id'] for r in records})
                    for record in records:
                        assert all(record[k] == population[record['id']][k] for k in population[record['id']])
                    audit_metrics(records, arms[arm]['metrics'])
                    panels_checked += 1
                delta = arms['selected']['metrics']['balanced_accuracy'] - arms['initial']['metrics']['balanced_accuracy']
                assert math.isclose(delta, arms['change']['balanced_accuracy'], abs_tol=1e-12)
    print(json.dumps(dict(verified_files=len(manifest['files']),
                         validation_predictions=predictions_checked,
                         test_model_arm_panels=panels_checked,
                         policy_selection='Matches registered validation rule',
                         paid_requests=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', default='reports/stepguard-native')
    main(parser.parse_args().bundle)
