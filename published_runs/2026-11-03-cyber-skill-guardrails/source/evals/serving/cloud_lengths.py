"""Bounded matched-token serving pilot. Synthetic length inputs have no labels."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import time

import httpx
import numpy as np


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def write_rows(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(x) + '\n' for x in values))


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def summary(records, elapsed, hourly_rate=.59):
    good = [r for r in records if r.get('prediction') in ('ALLOW', 'BLOCK')]
    lat = [r['seconds'] * 1000 for r in good]
    rate = len(good) / elapsed
    return dict(requests=len(records), valid=len(good), errors=len(records)-len(good),
                wall_seconds=elapsed, requests_per_second=rate,
                p50_ms=float(np.quantile(lat, .5)) if lat else None,
                p95_ms=float(np.quantile(lat, .95)) if lat else None,
                gpu_usd_per_million=hourly_rate/3600/rate*1e6 if rate else None,
                prompt_tokens=sum(r.get('usage', {}).get('prompt_tokens', 0) for r in good),
                completion_tokens=sum(r.get('usage', {}).get('completion_tokens', 0) for r in good))


def prepare(state):
    from transformers import AutoTokenizer
    from evals.qwen_policy.run import render
    reg = json.loads((state/'registration.json').read_text())
    spec = reg['model']
    tok = AutoTokenizer.from_pretrained(spec['model'], revision=spec['revision'])
    policy = json.loads((state/'policy.json').read_text())
    def encode(content, name):
        messages = [dict(role='system', content=render(policy)),
                    dict(role='user', content=json.dumps({'request': content}, ensure_ascii=False))]
        ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                      enable_thinking=False, return_dict=False)
        assert isinstance(ids, list) and all(isinstance(x, int) for x in ids)
        return dict(id=name, token_ids=ids, input_sha256=sha(ids), full_tokens=len(ids))
    fit = rows(state/'private-fit.jsonl')[:64]
    write_rows(state/'private-inputs/fit.jsonl', [encode(r['prompt'], r['id']) for r in fit])
    sentences = [
        'The support team reviewed the document before the weekly meeting.',
        'Please summarize the available information and identify the missing details.',
        'A manager asked for a clear description of the proposed workflow.',
        'The archive contains notes about projects, training, schedules and equipment.',
        'Compare the two options using the information in the attached report.',
        'Each department keeps records of changes and the reasons for those decisions.',
        'The user wants a concise explanation that colleagues can understand.',
        'Identify the dates, dependencies and questions that need further discussion.',
    ]
    groups = {}
    for length in reg['content_lengths']:
        group = []
        for i in range(64):
            rng = random.Random(20261101 + length*100 + i)
            text = f'Document {length} number {i}. ' + ' '.join(rng.choice(sentences) for _ in range(600))
            content_ids = tok.encode(text, add_special_tokens=False)[:length]
            content = tok.decode(content_ids)
            row = encode(content, f'synthetic-{length}-{i}')
            row['content_tokens'] = len(tok.encode(content, add_special_tokens=False))
            assert row['content_tokens'] == length
            assert row['full_tokens'] + 8 <= 8192
            group.append(row)
        groups[str(length)] = group
    groups['mixed'] = [groups[str(n)][i] for n in reg['content_lengths'] for i in range(16)]
    for name, group in groups.items():
        write_rows(state/f'private-inputs/{name}.jsonl', group)
    manifest = {}
    for p in sorted((state/'private-inputs').glob('*.jsonl')):
        data = rows(p)
        assert len({r['input_sha256'] for r in data}) == len(data)
        manifest[p.stem] = [dict((k,v) for k,v in r.items() if k!='token_ids') for r in data]
    write(state/'input-manifest.json', manifest)
    write(state/'input-freeze.json', dict(registration_sha256=sha(reg), policy_sha256=sha(policy),
        manifest_sha256=sha(manifest), tokenizer_class=type(tok).__name__,
        input_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (state/'private-inputs').glob('*.jsonl')}))


class Client:
    def __init__(self, model):
        self.model = model
        self.http = httpx.Client(timeout=180, limits=httpx.Limits(max_connections=32,
                                                                max_keepalive_connections=32))

    def one(self, row):
        start = time.perf_counter()
        result = {k:v for k,v in row.items() if k!='token_ids'}
        try:
            req = dict(model=self.model, prompt=row['token_ids'], max_tokens=8,
                       temperature=0, top_p=1, seed=42, stream=False,
                       add_special_tokens=False)
            response = self.http.post('http://127.0.0.1:8000/v1/completions', json=req)
            response.raise_for_status()
            value = response.json()
            choice = value['choices'][0]
            result.update(text=choice.get('text'), finish_reason=choice.get('finish_reason'),
                          usage=value.get('usage', {}))
            if result['usage'].get('prompt_tokens') != row['full_tokens']:
                raise ValueError('Server prompt token count differs from frozen input')
            if choice['finish_reason']!='stop' or choice['text'].strip() not in ('A','B'):
                raise ValueError('Classification contract failed')
            result['prediction'] = 'ALLOW' if choice['text'].strip()=='A' else 'BLOCK'
        except Exception as exc:
            result.update(prediction='ERROR', error=type(exc).__name__+': '+str(exc)[:350])
        result['seconds'] = time.perf_counter()-start
        return result

    def run(self, data, concurrency, output, seed):
        shuffled = list(data)
        random.Random(seed).shuffle(shuffled)
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            records = list(pool.map(self.one, shuffled))
        elapsed = time.perf_counter()-start
        write_rows(output.with_suffix('.jsonl'), records)
        result = dict(summary(records, elapsed), concurrency=concurrency, seed=seed)
        write(output.with_suffix('.json'), result)
        print(json.dumps(dict(run=output.name, **result)), flush=True)
        return records, result


@contextmanager
def server(state, engine, parameter):
    reg = json.loads((state/'registration.json').read_text())
    spec = reg['model']
    env = os.environ.copy()
    env['TOKENIZERS_PARALLELISM'] = 'false'
    if engine=='vllm':
        env['PATH'] = '/root/vllmenv/bin:'+env.get('PATH','')
        env['CUDA_HOME'] = '/root/vllmenv/lib/python3.12/site-packages/nvidia/cu13'
        command = ['/root/vllmenv/bin/vllm', 'serve', spec['model'], '--revision', spec['revision'],
            '--host', '127.0.0.1', '--port', '8000', '--dtype', 'bfloat16', '--max-model-len', '8192',
            '--gpu-memory-utilization', '.85', '--max-num-seqs', '32', '--max-num-batched-tokens', str(parameter),
            '--no-enable-prefix-caching', '--language-model-only']
    else:
        python = (state/'runtime/sglang-python.txt').read_text().strip()
        env['PATH'] = str(Path(python).parent)+':'+env.get('PATH','')
        env['CUDA_HOME'] = '/root/vllmenv/lib/python3.12/site-packages/nvidia/cu13'
        command = [python, '-m', 'sglang.launch_server', '--model-path', spec['model'],
            '--revision', spec['revision'], '--host', '127.0.0.1', '--port', '8000', '--dtype', 'bfloat16',
            '--context-length', '8192', '--mem-fraction-static', '.85', '--max-running-requests', '32',
            '--chunked-prefill-size', str(parameter), '--max-prefill-tokens', '8192',
            '--disable-radix-cache', '--cuda-graph-max-bs-decode', '32']
    runtime = state/'runtime'; runtime.mkdir(exist_ok=True)
    stem = f'{engine}-p{parameter}-{time.time_ns()}'
    start = time.perf_counter()
    with (runtime/(stem+'.log')).open('w') as out:
        proc = subprocess.Popen(command, stdout=out, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True)
        try:
            for _ in range(300):
                if proc.poll() is not None:
                    raise RuntimeError('Server exited: '+stem)
                try:
                    r = httpx.get('http://127.0.0.1:8000/health', timeout=2)
                    if r.status_code==200: break
                except httpx.HTTPError: pass
                time.sleep(2)
            else: raise RuntimeError('Startup timeout: '+stem)
            write(runtime/(stem+'.json'), dict(command=command, ready_seconds=time.perf_counter()-start))
            yield
        finally:
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            time.sleep(2)


def run(state, engine):
    reg = json.loads((state/'registration.json').read_text())
    freeze = json.loads((state/'input-freeze.json').read_text())
    assert freeze['registration_sha256']==sha(reg)
    for name,digest in freeze['input_files'].items():
        assert hashlib.sha256((state/'private-inputs'/name).read_bytes()).hexdigest()==digest
    fit = rows(state/'private-inputs/fit.jsonl')
    out = state/engine; out.mkdir(exist_ok=True)
    candidates = []
    for parameter in (2048,8192):
        try:
            with server(state, engine, parameter):
                client = Client(reg['model']['model'])
                warm = [client.one(r) for r in fit[:8]]
                if any(r['prediction']=='ERROR' for r in warm):
                    write_rows(out/f'warmup-failed-p{parameter}.jsonl', warm)
                    raise RuntimeError('Warm-up output contract failed')
                parity, _ = client.run(fit[:32], 1, out/f'parity-p{parameter}', 41)
                batched, result = client.run(fit, 16, out/f'tune-p{parameter}', 42)
                lookup = {r['id']:r for r in batched}
                changes = sum(r['prediction']!=lookup[r['id']]['prediction'] for r in parity)
                result['decision_changes'] = changes
                if result['errors'] or changes>1:
                    raise RuntimeError('Fitting batch consistency gate failed')
                candidates.append(dict(parameter=parameter, **result))
        except Exception as exc:
            write(out/f'failed-p{parameter}.json', dict(error=str(exc)))
    if not candidates: raise RuntimeError('No accepted configuration for '+engine)
    selected = max(candidates, key=lambda r:r['requests_per_second'])
    write(out/'freeze.json', dict(selected=selected, candidates=candidates,
        rule='highest fitting valid requests/sec; no errors; at most one batch label change'))
    with server(state, engine, selected['parameter']):
        client = Client(reg['model']['model'])
        for r in fit[:16]: client.one(r)
        for repeat in range(2):
            groups = [str(n) for n in reg['content_lengths']]+['mixed']
            if repeat: groups.reverse()
            for name in groups:
                data = rows(state/f'private-inputs/{name}.jsonl')
                for c in ([1,8,32] if repeat==0 else [32,8,1]):
                    # Warm each sequence-length/batch condition before timing.
                    with ThreadPoolExecutor(max_workers=c) as pool:
                        warm = list(pool.map(client.one, data[:min(max(8,c),len(data))]))
                    if any(r['prediction']=='ERROR' for r in warm):
                        write_rows(out/f'length-warmup-failed-{name}-c{c}-r{repeat}.jsonl', warm)
                    client.run(data, c, out/f'measure-{name}-c{c}-r{repeat}', 100+repeat)
    write(out/'complete.json', dict(engine=engine, status='completed'))


if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--action', choices=['prepare','vllm','sglang'], required=True)
    a = p.parse_args()
    def stop(signum, frame): raise KeyboardInterrupt('Bounded pilot deadline')
    signal.signal(signal.SIGTERM, stop)
    if a.action=='prepare': prepare(a.state)
    else: run(a.state, a.action)
