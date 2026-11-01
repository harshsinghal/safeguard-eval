"""Native inference with exact-request caching and bounded API billing."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import threading
import time
import urllib.error
from .common import *


def fetch_api(body, api_key, uid, target, ledger, abort):
    from evals.jev import api
    if target.exists():
        return read(target)
    for attempt in range(3):
        attempt_id = uid if attempt == 0 else uid + '-retry' + str(attempt)
        with ledger.connect() as db:
            previous = db.execute('SELECT status FROM requests WHERE id=?', (attempt_id,)).fetchone()
        if previous:
            if previous[0] not in ('transport_upper_bound', 'retryable_http_upper_bound'):
                raise RuntimeError('Prior API attempt requires reconciliation before retry')
            continue
        if abort.is_set():
            raise RuntimeError('Aborted')
        ledger.reserve(attempt_id)
        try:
            response = api.post(body, api_key)
        except urllib.error.HTTPError as exc:
            retryable = exc.code in (408, 429, 500, 502, 503, 504)
            ledger.settle(attempt_id, api.RESERVE, 'retryable_http_upper_bound' if retryable else 'error_upper_bound')
            api.save(target.parent / (attempt_id + '.error.json'), {'http_status': exc.code, 'retryable': retryable})
            if not retryable:
                abort.set()
                raise RuntimeError('Jev HTTP ' + str(exc.code)) from None
        except Exception as exc:
            # A lost response can still be billed. Account the full reserved cost
            # before another separately reserved attempt; never assume it was free.
            ledger.settle(attempt_id, api.RESERVE, 'transport_upper_bound')
            api.save(target.parent / (attempt_id + '.error.json'), {'kind': 'transport', 'exception_type': type(exc).__name__})
        else:
            api.save(target, response)
            ledger.settle(attempt_id, api.billed_cost(response))
            return response
        if attempt < 2:
            time.sleep(2 ** attempt)
    abort.set()
    raise RuntimeError('Jev request exhausted three bounded attempts; partial results preserved')


def load_cache(state, model):
    cache = {}
    differences = []
    paths = sorted((state / f'cache/{model}').glob('*.jsonl*'))
    paths += sorted((state / f'predictions/{model}').glob('*.jsonl'))
    for path in paths:
        for r in rows(path):
            expected_model = MODELS[model]['resolved'] if model == 'jev' else MODELS[model]
            if r['model'] != expected_model:
                raise ValueError('Cached model differs')
            key = (r['id'], r['request_sha256'])
            if key in cache and (cache[key]['prediction'] != r['prediction'] or abs(cache[key]['score'] - r['score']) > 1e-6):
                differences.append({'id': r['id'], 'request_sha256': r['request_sha256'],
                    'retained_source': cache[key]['_cache_origin'], 'other_source': str(path.relative_to(state)),
                    'retained_prediction': cache[key]['prediction'], 'other_prediction': r['prediction'],
                    'absolute_score_difference': abs(cache[key]['score'] - r['score'])})
            # Prior API calls can vary despite identical requests. Retain the first
            # recorded response in sorted source-file/line order, without labels.
            cache.setdefault(key, {**r, '_cache_origin': str(path.relative_to(state))})
    write(state / f'runtime/{model}-cache-variation.json', {
        'policy': 'first response in sorted cache-file/line order; prior cache precedes new predictions',
        'varying_duplicates': differences})
    return cache


def infer(state, model, stage, split, vendor=None, keyfile=None, cap=2.0):
    state = Path(state)
    verify(state, test=split == 'test')
    manifest = read(state / f'jobs/{stage}-{split}-manifest.json')
    path = state / f'jobs/{model}/{stage}-{split}.jsonl.gz'
    if digest(path) != manifest['jobs'][model]:
        raise ValueError('Jobs changed')
    jobs = rows(path)
    out = state / f'predictions/{model}/{stage}-{split}.jsonl'
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = rows(out) if out.exists() else []
    done = {(r['id'], r['arm']): r for r in existing}
    if len(done) != len(existing):
        raise ValueError('Duplicate completed results')
    cache = load_cache(state, model)
    pending = {}
    aliases = defaultdict(list)
    for job in jobs:
        if hash_value(job['body']) != job['request_sha256']:
            raise ValueError('Changed body')
        if (job['id'], job['arm']) in done:
            if done[job['id'], job['arm']]['request_sha256'] != job['request_sha256']:
                raise ValueError('Changed resumed request')
            continue
        key = (job['id'], job['request_sha256'])
        aliases[key].append(job)
        if key not in cache:
            pending.setdefault(key, job)
    started = time.monotonic()
    cached_rows = 0
    engine = None
    ledger = None
    api_responses = 0
    native_forwards = 0
    with out.open('a') as handle:
        def emit(key, result, origin=None):
            nonlocal cached_rows
            if result['prediction'] not in ('ALLOW', 'BLOCK') or not math.isfinite(result['score']) or not 0 <= result['score'] <= 1:
                raise ValueError('Invalid decision')
            for job in aliases.pop(key):
                record = {k: v for k, v in result.items() if k not in ('id', 'arm', 'example_ids', 'body', 'request_sha256', 'prompt_sha256', '_cache_origin', 'cached_from')}
                record.update({k: v for k, v in job.items() if k != 'body'})
                record['model'] = MODELS[model]['resolved'] if model == 'jev' else MODELS[model]
                if origin:
                    record['cached_from'] = origin
                    cached_rows += 1
                handle.write(canonical(record) + '\n')
            handle.flush()
        for key in list(aliases):
            if key in cache:
                emit(key, cache[key], cache[key]['_cache_origin'])
        print(canonical({'model': model, 'stage': stage, 'split': split, 'jobs': len(jobs),
                         'cached_rows': cached_rows, 'new_unique_requests': len(pending)}), flush=True)
        if pending and model == 'jev':
            from evals.jev.api import Ledger, read_key, parse
            ledger = Ledger(state / 'jev-billing.sqlite', cap=cap)
            ledger.assert_no_pending()
            api_key = read_key(keyfile)
            raw = state / f'private-api/{stage}-{split}'
            raw.mkdir(parents=True, exist_ok=True)
            abort = threading.Event()
            def one(pair):
                key, job = pair
                if abort.is_set():
                    raise RuntimeError('Aborted')
                body = {'model': MODELS['jev']['model'], 'state': {'content': job['body']['content']},
                        'questions': {'moderation': job['body']['policy']}}
                if len(canonical(body).encode()) + 2048 > 32000:
                    raise ValueError('Request bound exceeded')
                uid = hash_value([stage, split, key, body])
                target = raw / (uid + '.json')
                response = fetch_api(body, api_key, uid, target, ledger, abort)
                result = parse(response, ['moderation'])['moderation']
                result.update({'response_id': response['id'], 'provider': response['provider'], 'api_request_sha256': hash_value(body)})
                return key, result
            try:
                with ThreadPoolExecutor(max_workers=8) as pool:
                    futures = [pool.submit(one, pair) for pair in pending.items()]
                    try:
                        for f in as_completed(futures):
                            key, result = f.result()
                            emit(key, result)
                            api_responses += 1
                            if api_responses % 250 == 0:
                                print(canonical({'model': model, 'stage': stage, 'new_done': api_responses,
                                                 'total_new': len(pending), 'accounted_usd': ledger.totals()['total_accounted_usd']}), flush=True)
                    except BaseException:
                        abort.set()
                        for f in futures:
                            f.cancel()
                        raise
            finally:
                write(state / 'jev-costs.json', ledger.totals())
        elif pending:
            from evals.retrieved_examples.native import Engine
            engine = Engine(model, vendor)
            batch_size = 8 if model == 'kev' else 1
            todo = list(pending.items())
            if split == 'smoke':
                sample = [j for _, j in sorted(todo, key=lambda p: -len(canonical(p[1]['body'])))[:16]]
                encoded = [engine.encode(j) for j in sample]
                serial = [engine.forward([e])[0] for e in encoded]
                batched = []
                for i in range(0, len(encoded), batch_size):
                    batched += engine.forward(encoded[i:i + batch_size])
                diff = max(abs(a['score'] - b['score']) for a, b in zip(serial, batched))
                changes = sum(a['prediction'] != b['prediction'] for a, b in zip(serial, batched))
                write(state / f'runtime/{model}-{stage}-parity.json', {'n': len(encoded), 'max_score_difference': diff,
                      'decision_changes': changes, 'batch_size': batch_size})
                if changes or diff > .005:
                    raise ValueError('Fitting batch parity failed; preserve before amendment')
            for i in range(0, len(todo), batch_size):
                batch = todo[i:i + batch_size]
                encoded = [engine.encode(j) for _, j in batch]
                values = engine.forward(encoded)
                if len(values) != len(batch):
                    raise ValueError('Missing native response')
                for (key, _), value in zip(batch, values):
                    emit(key, value)
                    native_forwards += 1
                if i % 128 == 0:
                    print(canonical({'model': model, 'stage': stage, 'split': split,
                                     'new_done': min(i + batch_size, len(todo)), 'total_new': len(todo)}), flush=True)
    if aliases:
        raise ValueError('Unfinished aliases')
    runtime = {'model': model, 'stage': stage, 'split': split, 'n': len(jobs), 'cached_rows_this_process': cached_rows,
               'api_responses_this_process': api_responses, 'native_requests_this_process': native_forwards,
               'seconds_this_process': time.monotonic() - started, 'prediction_sha256': digest(out), 'created_utc': now()}
    if engine is not None:
        runtime.update({'torch': engine.torch.__version__, 'gpu': engine.torch.cuda.get_device_name(), 'batch_size': batch_size})
    write(state / f'runtime/{model}-{stage}-{split}.json', runtime)
    print(canonical(runtime), flush=True)


from collections import defaultdict

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True)
    p.add_argument('--model', choices=MODELS, required=True)
    p.add_argument('--stage', choices=['format', 'retriever', 'selector', 'coverage', 'test'], required=True)
    p.add_argument('--split', choices=['smoke', 'validation', 'test'], required=True)
    p.add_argument('--vendor')
    p.add_argument('--keyfile')
    p.add_argument('--cap', type=float, default=2.0)
    infer(**vars(p.parse_args()))
