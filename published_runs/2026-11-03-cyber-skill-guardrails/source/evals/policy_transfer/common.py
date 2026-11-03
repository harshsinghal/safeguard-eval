"""Immutable identities and validation shared by the transfer experiment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from evals.wildguard.run import digest, read_rows
from evals.wildguard.metrics import report
from evals.qwen_policy.run import SETTINGS as QWEN_SETTINGS

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(__file__).with_name('registry.json')
FIELDS = ('purpose', 'block', 'allow', 'precedence')
EDITABLE = ('block', 'allow', 'precedence')
BASE = ROOT / 'evals/wildguard/policies/p0.json'
SPECIALIST_SETTINGS = dict(dtype='bfloat16', threshold=.5, retries=0,
    temperature=0, max_tokens=1, concurrency=32,
    native_windowing='PolicyLM upstream 2000-character windows; no character limit; max_batch_rows=1')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def sources():
    names = ['evals/run.py', 'evals/wildguard/run.py', 'evals/wildguard/metrics.py',
             'evals/qwen_policy/run.py']
    names += [str(p.relative_to(ROOT)) for p in sorted(Path(__file__).parent.glob('*.py'))]
    return {n: digest(ROOT / n) for n in names}


def settings(adapter):
    return QWEN_SETTINGS if adapter == 'qwen' else SPECIALIST_SETTINGS


def text_hash(policy):
    return hashlib.sha256(json.dumps({k: policy[k] for k in FIELDS},
                                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_policy(policy):
    base = read(BASE)
    if set(policy) != set(base):
        raise ValueError('Policy schema changed')
    for k in set(base) - set(EDITABLE) - {'id'}:
        if policy[k] != base[k]:
            raise ValueError('Task scaffold changed: ' + k)
    if any(not isinstance(v, str) or not v.strip() for v in policy.values()):
        raise ValueError('Missing policy field')
    if len(' '.join(policy.values()).split()) > 1500:
        raise ValueError('Oversized policy')
    return policy


def check_data(path, split):
    reg = read(REGISTRY)
    if digest(path) != reg['data_hashes'][split]:
        raise ValueError('Dataset bytes changed')
    rows = read_rows(path)
    if len(rows) != reg['counts'][split] or {r['split'] for r in rows} != {split}:
        raise ValueError('Wrong population')
    return rows


def load_run(folder, slug, policy, split):
    """Reject partial, altered, misaligned, or differently configured runs."""
    folder = Path(folder)
    reg = read(REGISTRY)
    model = reg['models'][slug]
    m = read(folder / 'manifest.json')
    s = read(folder / 'summary.json')
    rows = [json.loads(x) for x in (folder / 'predictions.jsonl').read_text().split('\n') if x]
    if (m['revision'] != model['revision'] or m['policy_sha256'] != digest(policy)
            or m['dataset_sha256'] != reg['data_hashes'][split] or m['split'] != split):
        raise ValueError('Run identity mismatch: ' + str(folder))
    if len(rows) != reg['counts'][split] or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Incomplete or duplicate run')
    if [r['id'] for r in rows] != m['ids'] or {r['split'] for r in rows} != {split}:
        raise ValueError('Run population mismatch')
    if not s.get('complete') or any(s[k] != v for k, v in report(rows).items()):
        raise ValueError('Summary does not reproduce')
    if folder.name == slug + '-' + split:
        b = reg['baseline'][slug][split]
        for filename, expected in b['files'].items():
            if digest(folder / filename) != expected:
                raise ValueError('Historical baseline changed')
    elif (m.get('model') != model['model'] or m.get('sources') != sources()
          or m.get('settings') != settings(model['adapter'])
          or m.get('registry_sha256') != digest(REGISTRY)):
        raise ValueError('Implementation or settings mismatch')
    return rows, s, m


def locate(state, slug, policy_id, split):
    state = Path(state)
    if policy_id == read(BASE)['id'] and split in ('fit', 'validation'):
        return state / 'baseline' / (slug + '-' + split)
    return state / 'runs' / (slug + '--' + policy_id + '--' + split)


def validate_freeze(path, slug, policy, data, split):
    if not path:
        raise ValueError('Final inference requires freeze')
    f = read(path)
    if (f.get('status') != 'frozen' or f['sources'] != sources()
            or f['registry_sha256'] != digest(REGISTRY)):
        raise ValueError('Freeze/source/registry changed')
    if digest(policy) not in f['policy_hashes'] or slug not in f['recipient_choice']:
        raise ValueError('Unregistered policy/model')
    if digest(data) != f['data_hashes'][split] or split not in ('audit', 'test'):
        raise ValueError('Unregistered final population')
    return f
