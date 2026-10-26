"""Identities, immutable files, and manifests for the HateXplain experiment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(__file__).with_name('registry.json')
SEED = 20261026


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().split('\n') if line]


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if path.exists() and path.read_text() != text:
        raise ValueError('Refusing to overwrite artifact: ' + str(path))
    path.write_text(text)


def write_rows(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in values)
    if path.exists() and path.read_text() != text:
        raise ValueError('Refusing to overwrite dataset')
    path.write_text(text)


def sources():
    files = [ROOT / 'evals/run.py', ROOT / 'evals/wildguard/run.py',
             ROOT / 'evals/wildguard/metrics.py', ROOT / 'evals/qwen_policy/run.py']
    files += sorted(Path(__file__).parent.glob('*.py'))
    return {str(p.relative_to(ROOT)): digest(p) for p in files}


def run_path(state, model, policy, variant, split, repeat=False):
    return Path(state) / 'runs' / '--'.join([model, policy, variant, split] + (['repeat'] if repeat else []))
