"""Reproduce all staged selections and final metrics from prompt-free artifacts."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(archive):
    archive = Path(archive).resolve()
    checks = json.loads((archive / 'checksums.json').read_text())
    for rel, h in checks.items():
        if digest(archive / rel) != h:
            raise ValueError('Changed artifact: ' + rel)
    expected = json.loads((archive / 'results.json').read_text())
    with tempfile.TemporaryDirectory(prefix='retrieval-opt-verify-') as tmp:
        state = Path(tmp) / 'state'
        shutil.copytree(archive, state)
        for rel, info in json.loads((state / 'compressed-predictions.json').read_text()).items():
            dest = state / info['original_path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(gzip.decompress((state / rel).read_bytes()))
            if digest(dest) != info['uncompressed_sha256']:
                raise ValueError('Decompression mismatch')
        env = dict(os.environ, PYTHONPATH=str(state / 'source'))
        def run(action, stage=None):
            cmd = [sys.executable, '-m', 'evals.retrieval_optimization.study', action, '--state', str(state)]
            if stage:
                cmd += ['--stage', stage]
            subprocess.run(cmd, env=env, cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        for stage in ('format', 'retriever'):
            name = f'selection-{stage}.json'
            saved = json.loads((state / name).read_text())
            (state / name).unlink()
            run('select', stage)
            actual = json.loads((state / name).read_text())
            for key in ('selected', 'validation', 'hashes', 'registration_sha256'):
                if actual[key] != saved[key]:
                    raise ValueError('Stage selection mismatch: ' + stage + '/' + key)
            shutil.copy2(archive / name, state / name)
        frozen = json.loads((state / 'freeze.json').read_text())
        (state / 'freeze.json').unlink()
        run('freeze')
        actual = json.loads((state / 'freeze.json').read_text())
        for key in ('roles', 'configurations', 'validation', 'hashes', 'registration_sha256'):
            if actual[key] != frozen[key]:
                raise ValueError('Freeze mismatch: ' + key)
        shutil.copy2(archive / 'freeze.json', state / 'freeze.json')
        run('evaluate')
        actual = json.loads((state / 'results.json').read_text())
        for key in ('roles', 'configurations', 'test', 'validation', 'stages', 'paired'):
            if actual[key] != expected[key]:
                raise ValueError('Result mismatch: ' + key)
        diagnostic_names = ('validation-retrieval.json', 'policylm-validation-windows.json')
        saved_diagnostics = {name: json.loads((state / 'diagnostics' / name).read_text())
                             for name in diagnostic_names}
        subprocess.run([sys.executable, str(state / 'source/tools/diagnose_retrieval_optimization.py'),
                        '--state', str(state)], env=env, cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        for name, saved in saved_diagnostics.items():
            if json.loads((state / 'diagnostics' / name).read_text()) != saved:
                raise ValueError('Diagnostic mismatch: ' + name)
    result = {'verified': True, 'checksummed_files': len(checks), 'stage_selections': 'exact',
              'freeze': 'exact', 'metrics': 'exact', 'paired_intervals': 'exact',
              'validation_diagnostics': 'exact', 'paid_inference': False}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--archive', required=True)
    verify(**vars(p.parse_args()))
