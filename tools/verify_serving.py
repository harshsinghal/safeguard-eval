"""Audit the published serving experiment without GPU or inference API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.report_serving import report, trace
from tools.compare_serving_runtimes import compare


def read(path):
    return json.loads(Path(path).read_text())


def verify(archive):
    archive = Path(archive)
    passes = 0
    rejected_extensions = []
    requests = 0
    expected_models = {
        'reference': {'policylm', 'shieldstral', 'qwen-4b', 'wildguard', 'kev', 'clef', 'liquid'},
        'optimized': {'kev', 'clef'},
        'policy-batching': {'policylm'},
    }
    with tempfile.TemporaryDirectory(prefix='serving-audit-') as tmp:
        for kind, models in expected_models.items():
            state = archive / kind
            reg = read(state / 'registration.json')
            assert set(reg['models']) == models
            manifest = read(state / 'workload.json')['splits']
            fit = {r['prompt_sha256'] for r in manifest['tune']['ids']}
            measured = {r['id']: r['prompt_sha256'] for r in manifest['measure']['ids']}
            assert len(fit) == 96 and len(measured) == 384
            assert len(set(measured.values())) == 384
            assert not fit.intersection(measured.values())
            for slug, spec in reg['models'].items():
                directory = state / slug
                if 'policy_sha256' in spec:
                    assert hashlib.sha256((state / 'policies' / (slug + '.json')).read_bytes()).hexdigest() == spec['policy_sha256']
                if not (directory / 'complete.json').exists():
                    assert kind == 'policy-batching' and slug == 'policylm'
                    assert read(directory / 'failed-p8.json')['error'] == 'Batch parity needs investigation'
                    assert read(directory / 'parity-check-p8.json')['max_score_difference'] > .02
                    assert read(directory / 'failed-p32.json')['error'] == 'Matching-concurrency warm-up failed'
                    assert not (directory / 'freeze.json').exists()
                    assert not list(directory.glob('measure-*.json'))
                    rejected_extensions.append(kind + '/' + slug)
                    continue
                frozen = read(directory / 'freeze.json')
                valid = [r for r in frozen['tuning'] if r['errors'] == 0]
                assert frozen['parameter'] == max(valid, key=lambda r: r['requests_per_second'])['parameter']
                assert frozen['measurement_input_hash'] == reg['inputs']['measure']
                conditions = {(False, c, r) for c in (1, 8, 32, 64) for r in range(3)}
                if spec['backend'] == 'vllm':
                    assert (directory / 'cached-curve-complete.json').exists()
                    conditions |= {(True, c, r) for c in (1, 8, 32, 64) for r in range(3)}
                actual = set()
                for path in directory.glob('measure-*.json'):
                    saved = read(path)
                    records = trace(path.with_suffix('.jsonl'))
                    assert len(records) == 384
                    assert {r['id']: r['prompt_sha256'] for r in records} == measured
                    actual.add((saved['cache'], saved['concurrency'], saved['seed'] - 100))
                    passes += 1
                    requests += len(records)
                assert actual == conditions, (kind, slug, actual ^ conditions)
            destination = Path(tmp) / kind
            report(state, destination)
            for name in ('summary.json', 'repeat-parity.json'):
                assert read(destination / name) == read(archive / 'analysis' / kind / name)
            if (destination / 'results.csv').exists():
                assert (destination / 'results.csv').read_bytes() == (archive / 'analysis' / kind / 'results.csv').read_bytes()
            else:
                assert not (archive / 'analysis' / kind / 'results.csv').exists()
        for kind in ('optimized', 'policy-batching'):
            dest = Path(tmp) / (kind + '-comparison.json')
            compare(archive / 'reference', archive / kind, dest)
            assert read(dest) == read(archive / 'analysis' / dest.name)
    billing = read(archive / 'billing.json')
    assert billing['status'] == 'terminated'
    assert billing['new_total_usd'] <= 5
    assert abs(billing['prior_accounted_usd'] + billing['new_total_usd'] - billing['cumulative_accounted_usd']) < 1e-9
    assert billing['temporary_credentials_removed']
    assert billing['provider_instances_remaining'] == 0
    count = 0
    for line in (archive / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = archive / name
        assert path.is_relative_to(archive) and '..' not in Path(name).parts
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
        count += 1
    result = dict(status='passed', measured_passes=passes, measured_requests=requests,
                  unique_measurement_prompts=384, fitting_prompts=96,
                  checksummed_files=count, rejected_extensions=rejected_extensions,
                  paid_inference_calls=0,
                  note='Recomputes saved evidence; does not repeat GPU inference or assert classification accuracy.')
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', default='published_runs/2026-10-31-serving')
    verify(**vars(parser.parse_args()))
