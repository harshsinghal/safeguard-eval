"""Sequential GPU phases; audit/test files are needed only after a global freeze."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request

from evals.policy_transfer.common import REGISTRY, ROOT, load_run, locate, read
from evals.policy_transfer.study import candidates, freeze, policy_path, select


@contextmanager
def server(slug, state):
    spec = read(REGISTRY)['models'][slug]
    checkpoints = read(state / 'checkpoints.json')
    checkpoint = checkpoints[slug]
    if checkpoint['revision'] != spec['revision'] or checkpoint['model'] != spec['model']:
        raise ValueError('Checkpoint identity mismatch')
    if spec['adapter'] == 'policylm':
        yield checkpoint['path']
        return
    env = os.environ.copy()
    env['HF_HUB_OFFLINE'] = '1'
    env['CUDA_HOME'] = '/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13'
    command = ['/root/vllmenv/bin/vllm', 'serve', checkpoint['path'], '--served-model-name', spec['model'],
        '--host', '127.0.0.1', '--port', '8000', '--dtype', 'bfloat16',
        '--max-model-len', '32768', '--gpu-memory-utilization', '.90', '--max-num-seqs', '32', '--enforce-eager']
    if spec['adapter'] == 'qwen':
        command += ['--limit-mm-per-prompt', '{"image":0,"video":0}']
    logs = state / 'server-logs'
    logs.mkdir(exist_ok=True)
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
                raise RuntimeError('Server startup timed out: ' + slug)
            yield checkpoint['path']
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            time.sleep(3)


def job(state, slug, policy, split, checkpoint):
    out = locate(state, slug, read(policy)['id'], split)
    if out.exists():
        load_run(out, slug, policy, split)
        print('REUSE ' + out.name, flush=True)
        return
    py = '/root/policyenv/bin/python' if read(REGISTRY)['models'][slug]['adapter'] == 'policylm' else '/root/vllmenv/bin/python'
    command = [py, '-m', 'evals.policy_transfer.run', '--slug', slug,
        '--policy', str(policy), '--data', str(state / 'data' / (split + '.jsonl')),
        '--split', split, '--out', str(out), '--checkpoint', checkpoint]
    if split in ('audit', 'test'):
        command += ['--freeze', str(state / 'freeze.json')]
    subprocess.run(command, cwd=ROOT, check=True)


def main(state, phase):
    state = Path(state).resolve()
    if phase == 'author':
        from evals.policy_transfer.author import author
        with server('qwen-27b', state):
            author(state)
    elif phase == 'search':
        for slug in read(REGISTRY)['models']:
            with server(slug, state) as checkpoint:
                for policy in candidates(state, slug):
                    for split in ('fit', 'validation'):
                        job(state, slug, policy, split, checkpoint)
        select(state)
    elif phase in ('transfer', 'final'):
        selection = read(state / 'source-selection.json')
        if phase == 'final' and not (state / 'freeze.json').exists():
            raise ValueError('Transfer validation must finish before final inference')
        for slug in read(REGISTRY)['models']:
            with server(slug, state) as checkpoint:
                for entry in selection['pool']:
                    for split in (('validation',) if phase == 'transfer' else ('audit', 'test')):
                        job(state, slug, policy_path(state, entry), split, checkpoint)
        if phase == 'transfer':
            freeze(state)
    print('PHASE COMPLETE ' + phase, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', required=True)
    p.add_argument('--phase', required=True, choices=('author', 'search', 'transfer', 'final'))
    args = p.parse_args()
    main(args.state, args.phase)
