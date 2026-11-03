"""Native OpenRouter Decisions requests, strict parsing, durable bounded billing."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request

API = 'https://openrouter.ai/api/alpha/decisions'
MODEL = 'typesafe/jev-1.14'
RESOLVED = 'typesafe/jev-1.14-20261014'
PRICE = 0.042 / 1_000_000
CAP = 2.0
# Published maximum request context, including all questions, at the input rate.
RESERVE = 65_536 * PRICE


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def hash_value(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def payload(content, policies):
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Empty content')
    body = dict(model=MODEL, state={'content': content}, questions=policies)
    # Conservative bytes check; never silently truncate content or instructions.
    if len(canonical(body).encode()) + 2048 > 32_000:
        raise ValueError('Conservative context bound exceeded')
    return body


def probability(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1:
        raise ValueError('Invalid probability')
    return float(x)


def parse(response, policy_ids):
    if response.get('model') != RESOLVED or response.get('provider') != 'TypeSafe':
        raise ValueError('Unexpected model or provider; do not score another model as Jev')
    if set(response.get('answers', {})) != set(policy_ids):
        raise ValueError('Missing or additional question answers')
    out = {}
    for pid in policy_ids:
        a = response['answers'][pid]
        p = a.get('probabilities', {})
        if a.get('type') != 'choice' or set(p) != {'ALLOW', 'BLOCK'} or a.get('choice') not in p:
            raise ValueError('Wrong Choice schema')
        allow, block = probability(p['ALLOW']), probability(p['BLOCK'])
        if abs(allow + block - 1) > 1e-5:
            raise ValueError('Choice probabilities do not sum to one')
        if p[a['choice']] + 1e-7 < max(allow, block):
            raise ValueError('Choice is not an argmax')
        out[pid] = dict(prediction=a['choice'], score=block,
                        probabilities=p, confidence=probability(a['confidence']))
    return out


def billed_cost(response):
    u = response.get('usage', {})
    cost = u.get('cost')
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise ValueError('Missing/invalid billed cost; reservation remains outstanding')
    for name in ('input_tokens', 'output_tokens'):
        if not isinstance(u.get(name), int) or isinstance(u[name], bool) or u[name] < 0:
            raise ValueError('Invalid token accounting')
    if cost > RESERVE + 1e-12:
        raise ValueError('Bill exceeds reserved context charge')
    return float(cost)


class Ledger:
    """SQLite serializes concurrent reservations; crashes keep money reserved."""
    def __init__(self, path, initial_cost=0.0, cap=CAP):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cap = float(cap)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, cap REAL, initial REAL)')
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, reserved REAL, charged REAL, status TEXT)')
            db.execute('INSERT OR IGNORE INTO settings VALUES (1, ?, ?)', (cap, initial_cost))
            old = db.execute('SELECT cap, initial FROM settings WHERE id=1').fetchone()
            if old != (cap, initial_cost):
                raise ValueError('Existing budget configuration changed')

    def connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def reserve(self, uid):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            initial = db.execute('SELECT initial FROM settings WHERE id=1').fetchone()[0]
            total = db.execute('SELECT COALESCE(SUM(COALESCE(charged,reserved)),0) FROM requests').fetchone()[0]
            if initial + total + RESERVE > self.cap:
                raise RuntimeError('Jev study budget exhausted; no further request sent')
            db.execute('INSERT INTO requests VALUES (?, ?, NULL, ?)', (uid, RESERVE, 'pending'))

    def settle(self, uid, cost, status='reported'):
        if not math.isfinite(cost) or not 0 <= cost <= RESERVE:
            raise ValueError('Uncovered cost')
        with self.connect() as db:
            cur = db.execute('UPDATE requests SET charged=?,status=? WHERE id=? AND status=?',
                             (cost, status, uid, 'pending'))
            if cur.rowcount != 1:
                raise ValueError('Missing or duplicate settlement')

    def totals(self):
        with self.connect() as db:
            initial = db.execute('SELECT initial FROM settings WHERE id=1').fetchone()[0]
            rr = db.execute('SELECT status,COUNT(*),SUM(COALESCE(charged,reserved)) FROM requests GROUP BY status').fetchall()
        return dict(cap_usd=self.cap, initial_usd=initial,
                    total_accounted_usd=initial + sum(r[2] for r in rr),
                    statuses={r[0]: dict(requests=r[1], usd=r[2]) for r in rr})

    def assert_no_pending(self):
        if self.totals()['statuses'].get('pending', {}).get('requests', 0):
            raise RuntimeError('Unreconciled request; inspect raw response and billing before resuming')


def read_key(path):
    keys = set(re.findall(r'sk-or-v1-[A-Za-z0-9_-]+', Path(path).read_text()))
    if len(keys) != 1:
        raise ValueError('Expected one OpenRouter key; no values are logged')
    return keys.pop()


def post(body, key):
    req = urllib.request.Request(API, data=canonical(body).encode(), headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
        'X-OpenRouter-Title': 'Safeguard Eval Jev benchmark'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def infer(state, dataset, split, records, policies, keyfile, concurrency=8):
    """Resume only verified successes; every retry is a separately reserved attempt."""
    state = Path(state)
    initial = json.loads((state/'connectivity.json').read_text())['response']['usage']['cost']
    ledger = Ledger(state/'billing.sqlite', initial)
    ledger.assert_no_pending()
    key = read_key(keyfile)
    output = state/'runs'/dataset/split
    raw = output/'raw'
    raw.mkdir(parents=True, exist_ok=True)
    abort = threading.Event()

    def one(row):
        if abort.is_set():
            raise RuntimeError('Run stopped')
        body = payload(row['prompt'], policies)
        request_hash = hash_value(body)
        uid = hash_value([dataset, split, row['id'], request_hash])
        final = raw/(uid + '.json')
        if final.exists():
            record = json.loads(final.read_text())
            if record['request_sha256'] != request_hash:
                raise ValueError('Request cache mismatch')
            parsed = parse(record['response'], policies)
        else:
            for attempt in range(3):
                if abort.is_set():
                    raise RuntimeError('Run stopped')
                attempt_id = uid + '-' + str(attempt)
                ledger.reserve(attempt_id)
                t0 = time.perf_counter()
                try:
                    response = post(body, key)
                except urllib.error.HTTPError as exc:
                    # No provider error body or header can leak credentials into logs.
                    evidence = dict(request_sha256=request_hash, status=exc.code, attempt=attempt,
                                    latency_seconds=time.perf_counter()-t0)
                    save(raw/(attempt_id + '.error.json'), evidence)
                    # Conservatively charge the reservation; do not claim failed HTTP is free.
                    ledger.settle(attempt_id, RESERVE, 'error_upper_bound')
                    if exc.code == 429 and attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    abort.set()
                    raise RuntimeError(f'HTTP {exc.code}; stopped before generating a misleading score') from None
                except Exception as exc:
                    save(raw/(attempt_id + '.error.json'), dict(request_sha256=request_hash,
                        error_type=type(exc).__name__, attempt=attempt))
                    # Pending reservation deliberately remains; billing may be unknown.
                    abort.set()
                    raise RuntimeError('Transport/decoding failure; reconcile reservation') from None
                record = dict(id=row['id'], request_sha256=request_hash, attempt_id=attempt_id,
                              latency_seconds=time.perf_counter()-t0, response=response)
                # Preserve response even if identity, schema, or billing validation fails.
                save(raw/(attempt_id + '.response.json'), record)
                try:
                    cost = billed_cost(response)
                    ledger.settle(attempt_id, cost)
                    parsed = parse(response, policies)
                except Exception:
                    abort.set()
                    raise
                save(final, record)
                break
        meta = {k: v for k, v in row.items() if k != 'prompt'}
        return {pid: dict(meta, **values, model=record['response']['model'],
                         provider=record['response']['provider'], request_sha256=request_hash,
                         response_id=record['response']['id']) for pid, values in parsed.items()}

    predictions = {pid: [] for pid in policies}
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one, row) for row in records]
        try:
            for i, future in enumerate(as_completed(futures), 1):
                for pid, row in future.result().items():
                    predictions[pid].append(row)
                if i % 250 == 0 or i == len(records):
                    print(dataset, split, i, '/', len(records), ledger.totals()['total_accounted_usd'], flush=True)
        except BaseException:
            abort.set()
            for f in futures:
                f.cancel()
            raise
    for pid, rr in predictions.items():
        rr.sort(key=lambda r: r['id'])
        target = output/(pid + '.jsonl')
        target.write_text(''.join(canonical(r) + '\n' for r in rr))
    save(state/'costs.json', ledger.totals())
    return predictions
