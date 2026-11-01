"""Publish the staged study without source prompts, vectors or credentials."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import hashlib

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def package(state, output):
    state, output = Path(state), Path(output)
    if output.exists():
        raise ValueError('Use a new immutable archive')
    if not (state / 'results.json').exists() or json.loads((state / 'cleanup.json').read_text())['our_instance_active']:
        raise ValueError('Complete results and resource termination required')
    output.mkdir(parents=True)
    compressed = {}
    def copy(path, relative=None):
        relative = relative or path.relative_to(state)
        dest = output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.jsonl':
            dest = dest.with_suffix('.jsonl.gz')
            dest.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
            compressed[str(dest.relative_to(output))] = {'original_path': str(relative), 'uncompressed_sha256': digest(path)}
        else:
            shutil.copy2(path, dest)
    for name in ('registration.json', 'freeze.json', 'selection-format.json', 'selection-retriever.json',
                 'results.json', 'RESULTS.md', 'bank-audit.json', 'bank-short-metadata.jsonl.gz',
                 'bank-expanded-metadata.jsonl.gz', 'billing.json', 'cleanup.json', 'jev-costs.json'):
        copy(state / name)
    for name in ('policies', 'metadata', 'cache', 'predictions', 'runtime', 'retrieval', 'rerank', 'amendments'):
        for path in sorted((state / name).rglob('*')):
            if path.is_file():
                copy(path)
    for path in sorted(state.glob('registration-v*.json')):
        copy(path)
    for path in sorted((state / 'jobs').glob('*-manifest.json')):
        copy(path)
    reg = json.loads((state / 'registration.json').read_text())
    for rel, h in reg['sources'].items():
        if digest(ROOT / rel) != h:
            raise ValueError('Registered source changed: ' + rel)
        dest = output / 'source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
        parent = Path(rel).parent
        while str(parent) != '.':
            init = ROOT / parent / '__init__.py'
            if init.exists():
                shutil.copy2(init, output / 'source' / parent / '__init__.py')
            parent = parent.parent
    for rel in ('tools/package_retrieval_optimization.py', 'tools/verify_retrieval_optimization.py',
                'tests/test_retrieval_optimization.py'):
        dest = output / 'source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    for name in ('PLAN.md', 'NOTES.md', 'RUNNING.md'):
        shutil.copy2(ROOT / 'docs/retrieval-optimization' / name, output / name)
    (output / 'compressed-predictions.json').write_text(json.dumps(compressed, indent=2) + '\n')
    (output / 'README.md').write_text('# Staged retrieval optimization evidence\n\n'
        'Model-specific formatting, stronger embeddings, example selection, and library coverage '
        'with fixed classifier weights and decision rules. See [results](RESULTS.md), [plan](PLAN.md), '
        '[notes](NOTES.md), [costs](billing.json), and [cleanup](cleanup.json).\n\n'
        'Source prompts, vectors, request bodies, API response bodies and credentials are excluded. '
        'Example IDs, scores, request hashes and prediction provenance are retained.\n\n'
        'Reproduce with NumPy on CPU, without model downloads or credentials:\n\n```bash\n'
        f'python3 tools/verify_retrieval_optimization.py --archive {output.relative_to(ROOT)}\n```\n')
    checks = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'checksums.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps({'files': len(checks), 'bytes': sum(p.stat().st_size for p in output.rglob('*') if p.is_file())}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True)
    p.add_argument('--output', required=True)
    package(**vars(p.parse_args()))
