"""OpenRouter classification with strict outputs, frozen finals and durable billing."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import fcntl
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

from evals.qwen_policy.run import render
from evals.wildguard.run import digest, read_rows
from evals.wildguard.metrics import report

SETTINGS = dict(concurrency=1, retries=0, max_tokens=8192, temperature='omitted',
                primary='strict free-generated A=ALLOW/B=BLOCK', reasoning_text='excluded',
                provider_fallbacks=False, structured_output=False)
API = 'https://openrouter.ai/api/v1/chat/completions'
PUBLIC_FIELDS = ('id', 'group', 'split', 'expected', 'adversarial', 'subcategory')


def now():
    return datetime.now(timezone.utc).isoformat()


def sources():
    root = Path(__file__).parents[1]
    names = ['frontier_api/run.py', 'frontier_api/study.py', 'frontier_api/pilot.py', 'qwen_policy/run.py',
             'wildguard/run.py', 'wildguard/metrics.py', 'run.py']
    return {name: digest(root / name) for name in names}


def identity(registry, arm):
    a = registry['arms'][arm]
    return dict(arm=a, model=registry['models'][a['model_key']], settings=SETTINGS)


def payload(registry, arm, policy, prompt):
    config = identity(registry, arm)
    m, a = config['model'], config['arm']
    reasoning = m['reasoning']
    effort = a['effort']
    if effort not in reasoning['supported_efforts']:
        raise ValueError('Unsupported reasoning effort')
    if effort == 'none' and reasoning.get('mandatory'):
        raise ValueError('This model cannot turn reasoning off')
    if m['max_tokens'] != SETTINGS['max_tokens']:
        raise ValueError('Unregistered output budget')
    if not {'reasoning', 'max_tokens'} <= set(m['supported_parameters']):
        raise ValueError('Endpoint lacks required controls')
    price = m['price_ceiling_per_token']
    return dict(model=m['id'], messages=[dict(role='system', content=render(policy)),
        dict(role='user', content=json.dumps({'request': prompt}, ensure_ascii=False))],
        max_tokens=SETTINGS['max_tokens'], reasoning=dict(effort=effort, exclude=True),
        provider=dict(only=[m['provider_tag']], ignore=m['excluded_provider_tags'],
                      allow_fallbacks=False, require_parameters=True,
                      max_price=dict(prompt=price['prompt'] * 1e6,
                                     completion=price['completion'] * 1e6,
                                     request=price['request'])))


def parse(response):
    if len(response.get('choices', [])) != 1:
        raise ValueError('Expected exactly one classification')
    choice = response['choices'][0]
    message = choice['message']
    if choice.get('finish_reason') != 'stop' or message.get('refusal') or message.get('tool_calls'):
        raise ValueError('Refused, truncated, or non-classification response')
    content = message.get('content')
    if not isinstance(content, str) or content.strip() not in ('A', 'B'):
        raise ValueError('Invalid classification')
    return 'ALLOW' if content.strip() == 'A' else 'BLOCK'


def micros(value):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        raise ValueError('Invalid cost')
    return int((value * 1000000).to_integral_value(rounding=ROUND_CEILING))


def reserve_usd(request, model):
    # Deliberately overestimates typical token counts. Check actual usage at every step.
    input_bound = len(json.dumps(request['messages'], ensure_ascii=False).encode()) + 512
    if input_bound + request['max_tokens'] > model['context_length']:
        raise ValueError('Conservative context bound exceeded; do not truncate')
    p = model['price_ceiling_per_token']
    input_price = max(p['prompt'], p.get('input_cache_write', 0), p.get('input_cache_write_1h', 0))
    return input_bound * input_price + request['max_tokens'] * p['completion'] + p['request']


class Ledger:
    """One shared append-only study ledger. Pending charges remain reserved after crashes."""
    def __init__(self, path, cap):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cap = micros(cap)
        self.lock = self.path.with_suffix('.lock')

    @contextmanager
    def locked(self):
        with self.lock.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            events = [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []
            if not events:
                self.append(dict(event='init', cap_microusd=self.cap, created_utc=now()))
            elif events[0]['cap_microusd'] != self.cap:
                raise ValueError('Ledger cap changed; reconcile explicitly')
            yield events

    def append(self, event):
        with self.path.open('a') as f:
            f.write(json.dumps(event) + '\n')
            f.flush()
            import os
            os.fsync(f.fileno())

    @staticmethod
    def charges(events):
        charges = {}
        for e in events:
            if e['event'] in ('reserve', 'settle'):
                charges[e['request_id']] = e['microusd']
        return charges

    def reserve(self, request_id, dollars):
        amount = micros(dollars)
        with self.locked() as events:
            charges = self.charges(events)
            pending = {e['request_id'] for e in events if e['event'] == 'reserve'} - {
                e['request_id'] for e in events if e['event'] == 'settle'}
            if pending:
                raise ValueError('Unreconciled request; stop before more paid work')
            if request_id in charges:
                raise ValueError('Request already attempted; no hidden retry')
            if sum(charges.values()) + amount > self.cap:
                raise ValueError('Study budget cannot cover next request')
            self.append(dict(event='reserve', request_id=request_id, microusd=amount, created_utc=now()))

    def settle(self, request_id, dollars, cost_status='reported'):
        amount = micros(dollars)
        with self.locked() as events:
            charges = self.charges(events)
            if request_id not in charges or any(e['event'] == 'settle' and e['request_id'] == request_id for e in events):
                raise ValueError('Missing or already settled reservation')
            reserved = charges[request_id]
            self.append(dict(event='settle', request_id=request_id, microusd=amount,
                             cost_status=cost_status, created_utc=now()))
            if amount > reserved:
                raise ValueError('Actual billing exceeds reservation; review before continuing')


def read_key(path):
    found = set(re.findall(r'sk-or-v1-[A-Za-z0-9_-]+', Path(path).read_text()))
    if len(found) != 1:
        raise ValueError('Expected one OpenRouter key; values are never logged')
    return found.pop()


def post(request, key):
    req = urllib.request.Request(API, data=json.dumps(request).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                 'X-OpenRouter-Title': 'Safeguard Eval frontier classification'})
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)


def validate_freeze(path, registry, arm, policy_hash, data, split):
    if not path:
        raise ValueError('Final inference requires a freeze')
    f = json.loads(Path(path).read_text())
    r = json.loads(Path(registry).read_text())
    if f['status'] != 'frozen' or f['registry_sha256'] != digest(registry) or f['sources'] != sources():
        raise ValueError('Changed registry or implementation')
    if f['identities'][arm] != identity(r, arm) or policy_hash not in f['final_policy_hashes'][arm]:
        raise ValueError('Unregistered deployment or policy')
    if f['data_hashes'][split] != digest(data):
        raise ValueError('Changed held-out population')
    return f


def run(args):
    registry = json.loads(args.registry.read_text())
    rows = read_rows(args.data)
    split = {'pilot': 'fit', 'fit': 'fit', 'validation': 'validation', 'audit': 'audit', 'test': 'test', 'repeat': 'test'}[args.stage]
    if digest(args.data) != registry['data_hashes'][split] or len(rows) != registry['data_counts'][split]:
        raise ValueError('Wrong dataset hash or count')
    if {r['split'] for r in rows} != {split}:
        raise ValueError('Wrong split')
    if args.stage == 'pilot':
        rows = rows[:registry['pilot_n']]
        pilot_index = getattr(args, 'pilot_index', None)
        if pilot_index is not None:
            if not 0 <= pilot_index < len(rows):
                raise ValueError('Pilot index out of range')
            rows = rows[pilot_index:pilot_index + 1]
    elif args.stage == 'repeat':
        rows = rows[:256]
    policy = json.loads(args.policy.read_text())
    if len(' '.join(str(v) for v in policy.values()).split()) > 1500:
        raise ValueError('Oversized policy')
    policy_hash = digest(args.policy)
    if split in ('audit', 'test'):
        validate_freeze(args.freeze, args.registry, args.arm, policy_hash, args.data, split)
    elif not any(c['arm'] == args.arm and c['sha256'] == policy_hash for c in registry['candidates']):
        raise ValueError('Register candidate before inference')
    # Build every request before any billable action: catch unsupported settings/lengths locally.
    model = identity(registry, args.arm)['model']
    requests = [payload(registry, args.arm, policy, r['prompt']) for r in rows]
    bounds = [reserve_usd(p, model) for p in requests]
    if args.dry_run:
        result = dict(dry_run=True, n=len(rows), dataset_sha256=digest(args.data),
                      conservative_run_reservation_usd=sum(bounds), paid_requests=0)
        print(json.dumps(result))
        return result
    budget = registry['budget']
    if budget['status'] != 'approved' or not budget.get('authorization_note'):
        raise ValueError('Paid inference awaits an explicit study budget')
    if args.stage not in budget.get('allowed_stages', []):
        raise ValueError('This phase is not covered by the approved budget')
    ledger = Ledger(args.ledger, budget['approved_new_cap_usd'])
    key = read_key(args.key_file)
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = dict(created_utc=now(), arm=args.arm, identity=identity(registry, args.arm),
        policy_id=policy['id'], policy_sha256=policy_hash, dataset_sha256=digest(args.data),
        split=split, stage=args.stage, ids=[r['id'] for r in rows], sources=sources(),
        registry_sha256=digest(args.registry), freeze_sha256=digest(args.freeze) if args.freeze else None,
        input_fields=['prompt'], budget=budget, pilot_index=getattr(args, 'pilot_index', None))
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (args.out / 'policy.json').write_bytes(args.policy.read_bytes())
    outputs = []
    stop_reason = None
    started = time.monotonic()
    with (args.out / 'predictions.jsonl').open('x') as pred, (args.out / 'private-raw.jsonl').open('x') as raw:
        for case, request, bound in zip(rows, requests, bounds):
            row = {k: case[k] for k in PUBLIC_FIELDS if k in case}
            request_hash = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            request_id = hashlib.sha256((str(args.out.resolve()) + str(case['id']) + request_hash).encode()).hexdigest()
            try:
                ledger.reserve(request_id, bound)
            except ValueError as e:
                stop_reason = str(e)
                break
            row.update(request_sha256=request_hash, prediction='ERROR')
            response = None
            start = time.monotonic()
            fatal = False
            try:
                response = post(request, key)
                row['generation_id'] = response.get('id')
                row['served_model'] = response.get('model')
                row['provider'] = response.get('provider')
                choice = (response.get('choices') or [{}])[0]
                row['finish_reason'] = choice.get('finish_reason')
                usage = response.get('usage') or {}
                row['usage'] = {k: usage[k] for k in ('prompt_tokens', 'completion_tokens',
                    'completion_tokens_details', 'prompt_tokens_details', 'cost', 'cost_details') if k in usage}
                # No inferred zero cost: unknown charges remain reserved and stop the run.
                if 'cost' not in usage and row['finish_reason'] == 'content_filter':
                    # A filtered response is a scored failure, never retried. Deduct the entire
                    # pre-reserved ceiling until the provider supplies reconciled billing.
                    ledger.settle(request_id, bound, cost_status='conservative_content_filter_ceiling')
                    row['cost_upper_bound_usd'] = bound
                    row['billing_status'] = 'unreported; full request ceiling deducted'
                elif 'cost' not in usage:
                    raise RuntimeError('Missing billing')
                else:
                    ledger.settle(request_id, usage['cost'])
                if response.get('provider') != model['provider_name'] or response.get('model') not in model['allowed_response_models']:
                    raise RuntimeError('Unexpected provider/model')
                if args.arm.endswith('-lower') and registry['arms'][args.arm]['effort'] == 'none':
                    if (usage.get('completion_tokens_details') or {}).get('reasoning_tokens', 0) > 0:
                        raise RuntimeError('Reasoning reported for off arm')
                try:
                    row['prediction'] = parse(response)
                except (ValueError, KeyError, TypeError, IndexError):
                    row['error_type'] = 'ContentFiltered' if row['finish_reason'] == 'content_filter' else 'InvalidClassification'
            except Exception as e:
                row['error_type'] = type(e).__name__
                if isinstance(e, urllib.error.HTTPError):
                    row['http_status'] = e.code
                    try:
                        response = json.loads(e.read().decode())
                    except (ValueError, UnicodeError):
                        response = {'error': {'message': 'Non-JSON HTTP error; body omitted'}}
                # API/transport/config/billing errors abort; their attempted rows remain errors.
                fatal = True
            row['latency_seconds'] = time.monotonic() - start
            outputs.append(row)
            pred.write(json.dumps(row) + '\n'); pred.flush()
            raw.write(json.dumps(dict(id=case['id'], request=request, response=response), ensure_ascii=False) + '\n'); raw.flush()
            if fatal:
                stop_reason = 'Transport, routing, reasoning, or billing failure; reconcile before continuing'
                break
            if len(outputs) % 32 == 0:
                print(json.dumps(dict(completed=len(outputs), total=len(rows))), flush=True)
    result = report(outputs) if outputs else {'n': 0}
    result.update(complete=len(outputs) == len(rows) and stop_reason is None, stop_reason=stop_reason,
                  wall_seconds=time.monotonic() - started, attempted=len(outputs), expected=len(rows))
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('registry', 'data', 'policy', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--arm', required=True)
    p.add_argument('--stage', choices=('pilot', 'fit', 'validation', 'audit', 'test', 'repeat'), required=True)
    p.add_argument('--freeze', type=Path)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--pilot-index', type=int, help='One registered pilot row, for interleaved orchestration')
    p.add_argument('--ledger', type=Path, default=Path('work/frontier-api/spend.jsonl'))
    p.add_argument('--key-file', type=Path, default=Path.home() / 'workspace/KEYS/OPENROUTER_API.txt')
    print(json.dumps(run(p.parse_args())))
