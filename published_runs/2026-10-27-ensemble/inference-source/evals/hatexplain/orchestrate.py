"""Sequential GPU phases, with an explicit scope review and test-release gate."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request

from evals.hatexplain.common import REGISTRY, ROOT, digest, read, run_path
from evals.hatexplain.study import candidates, load_run


@contextmanager
def server(slug, state):
    spec = read(REGISTRY)['models'][slug]
    checkpoint = read(Path(state) / 'checkpoints.json')[slug]
    if checkpoint['revision'] != spec['revision'] or checkpoint['model'] != spec['model']:
        raise ValueError('Wrong checkpoint')
    if spec['adapter'] == 'policylm':
        yield checkpoint['path']
        return
    env = os.environ.copy(); env['HF_HUB_OFFLINE'] = '1'
    env['CUDA_HOME'] = '/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13'
    command = ['/root/vllmenv/bin/vllm', 'serve', checkpoint['path'], '--served-model-name', spec['model'],
        '--host', '127.0.0.1', '--port', '8000', '--dtype', 'bfloat16', '--max-model-len', '8192',
        '--gpu-memory-utilization', '.90', '--max-num-seqs', '32', '--enforce-eager']
    if spec['adapter'] == 'qwen':
        command += ['--limit-mm-per-prompt', '{"image":0,"video":0}']
    logs = Path(state) / 'server-logs'; logs.mkdir(exist_ok=True)
    with (logs / (slug + '-' + str(time.time_ns()) + '.log')).open('x') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            for _ in range(240):
                if process.poll() is not None:
                    raise RuntimeError('Server exited: ' + slug)
                try:
                    urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).close()
                    break
                except Exception:
                    time.sleep(3)
            else:
                raise RuntimeError('Server startup timed out')
            yield checkpoint['path']
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
            time.sleep(3)


def job(state, slug, identifier, variant, split, checkpoint, repeat=False):
    policy = state / 'policies' / (identifier + '.json')
    out = run_path(state, slug, identifier, variant, split, repeat)
    if out.exists():
        load_run(state, slug, policy, variant, split, repeat)
        print('REUSE ' + out.name, flush=True)
        return
    py = '/root/policyenv/bin/python' if slug == 'policylm' else '/root/vllmenv/bin/python'
    command = [py, '-m', 'evals.hatexplain.run', '--state', str(state), '--slug', slug,
        '--policy-path', str(policy), '--variant', variant, '--split', split, '--out', str(out), '--checkpoint', checkpoint]
    if repeat:
        command += ['--repeat']
    subprocess.run(command, cwd=ROOT, check=True)


def main(state, phase):
    state = Path(state).resolve(); reg = read(REGISTRY)
    if phase.startswith('author'):
        from evals.hatexplain.author import author
        with server('qwen-4b', state):
            author(state, int(phase[-1]))
    elif phase in ('baseline', 'fit1', 'fit2'):
        for slug in reg['models']:
            identifier = 'p0' if phase == 'baseline' else slug + '-p' + phase[-1]
            if not (state / 'policies' / (identifier + '.json')).exists():
                print('NO VALID CANDIDATE ' + identifier, flush=True)
                continue
            with server(slug, state) as checkpoint:
                job(state, slug, identifier, 'markdown', 'fit', checkpoint)
    elif phase == 'validation':
        review = read(state / 'eligibility.json')
        for slug in reg['models']:
            with server(slug, state) as checkpoint:
                for policy in candidates(state, slug):
                    entry = review[policy.stem]
                    if entry['policy_sha256'] != digest(policy):
                        raise ValueError('Scope review mismatch')
                    if entry['eligible']:
                        job(state, slug, policy.stem, 'markdown', 'validation', checkpoint)
    elif phase == 'final':
        frozen = read(state / 'freeze.json')
        for slug in reg['models']:
            with server(slug, state) as checkpoint:
                for item in frozen['jobs']:
                    if item['model'] == slug:
                        job(state, slug, item['policy_id'], item['variant'], 'test', checkpoint, item['repeat'])
    else:
        raise ValueError('Unknown phase')
    print('PHASE COMPLETE ' + phase, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--state', required=True)
    p.add_argument('--phase', required=True, choices=('baseline', 'author1', 'fit1', 'author2', 'fit2', 'validation', 'final'))
    main(**vars(p.parse_args()))
