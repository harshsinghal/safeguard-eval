"""Serial models, bounded tuning, then frozen repeated measurements."""
import argparse
import fcntl
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request
from evals.ensemble.common import read, rows, write, now, digest
from .client import Client

ENVS={'policylm':'policyenv','kev':'kevenv','clef':'clefenv','liquid':'liquidenv'}


@contextmanager
def server(state,slug,parameter,cache=False):
    spec=read(state/'registration.json')['models'][slug]
    start=time.perf_counter();env=os.environ.copy();env['TOKENIZERS_PARALLELISM']='false'
    if spec['backend']=='vllm':
        env['CUDA_HOME']='/root/vllmenv/lib/python3.12/site-packages/nvidia/cu13'
        env['PATH']='/root/vllmenv/bin:'+env.get('PATH','')
        # Benchmark-only localhost controls prevent repeated-content cache hits.
        env['VLLM_SERVER_DEV_MODE']='1'
        command=['/root/vllmenv/bin/vllm','serve',spec['model'],'--revision',spec['revision'],
            '--host','127.0.0.1','--port','8000','--dtype','bfloat16','--max-model-len','8192',
            '--gpu-memory-utilization','.85','--max-num-seqs','64','--max-num-batched-tokens',str(parameter),
            '--enable-prefix-caching' if cache else '--no-enable-prefix-caching']
        if slug in ('qwen-4b','shieldstral'):command+=['--language-model-only']
        # WildGuard requests already contain slow-tokenizer IDs from the client.
        # vLLM 0.32 no longer registers a server tokenizer mode named "slow".
    else:
        environment=spec.get('native_environment',ENVS[slug])
        command=['/root/'+environment+'/bin/python','-m','evals.serving.native','--state',str(state),'--model',slug,'--max-batch',str(parameter)]
    logs=state/'runtime';logs.mkdir(exist_ok=True)
    stem=f'{slug}-p{parameter}-cache{int(cache)}-{time.time_ns()}'
    with (logs/(stem+'.log')).open('w') as out:
        process=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:
            for _ in range(420):
                if process.poll() is not None:raise RuntimeError('Server exited; '+stem)
                try:
                    urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2).close();break
                except Exception:time.sleep(2)
            else:raise RuntimeError('Server startup timeout; '+stem)
            write(logs/(stem+'.json'),dict(model=slug,command=command,ready_seconds=time.perf_counter()-start,created_utc=now()))
            yield
        finally:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
            time.sleep(3)


def run(state,slug):
    state=Path(state);reg=read(state/'registration.json');spec=reg['models'][slug]
    for split,h in reg['inputs'].items():assert digest(state/'inputs'/(split+'.jsonl'))==h
    tune=rows(state/'inputs/tune.jsonl');measure=rows(state/'inputs/measure.jsonl')
    assert not {r['prompt_sha256'] for r in tune}&{r['prompt_sha256'] for r in measure}
    directory=state/slug;directory.mkdir(exist_ok=True)
    if (directory/'complete.json').exists():return
    candidates=reg['tuning_vllm_token_budgets'] if spec['backend']=='vllm' else reg['tuning_native_max_batches']
    tuning=[]
    if not (directory/'freeze.json').exists():
        for value in candidates:
            try:
                with server(state,slug,value):
                    client=Client(state,slug)
                    client.run(tune[:32],1,directory/f'parity-p{value}',seed=41)
                    result=client.run(tune,32,directory/f'tune-p{value}',seed=42)
                    reference=rows(directory/f'parity-p{value}.jsonl')
                    batched={r['id']:r for r in rows(directory/f'tune-p{value}.jsonl')}
                    differences=[abs(r['score']-batched[r['id']]['score']) for r in reference
                                 if r.get('score') is not None and batched[r['id']].get('score') is not None]
                    parity=dict(n=len(reference),decision_changes=sum(r['prediction']!=batched[r['id']]['prediction'] for r in reference),
                                max_score_difference=max(differences,default=0.))
                    write(directory/f'parity-check-p{value}.json',parity)
                    # Kernel variants must also agree with the fitting-only
                    # reference runtime before measurement inputs are timed.
                    cross_reference=state/'runtime-reference'/(slug+'.jsonl')
                    if cross_reference.exists():
                        previous={r['id']:r for r in rows(cross_reference)}
                        assert set(previous)=={r['id'] for r in reference}
                        assert all(r['prompt_sha256']==previous[r['id']]['prompt_sha256'] for r in reference)
                        cross=dict(n=len(reference),decision_changes=sum(r['prediction']!=previous[r['id']]['prediction'] for r in reference),
                            max_score_difference=max(abs(r['score']-previous[r['id']]['score']) for r in reference))
                        write(directory/f'runtime-parity-p{value}.json',cross)
                        if cross['max_score_difference']>.02 or cross['decision_changes']>1:
                            raise RuntimeError('Kernel runtime parity needs investigation')
                    # Qwen's primary classifier uses its generated A/B label.
                    # Record auxiliary probability drift without claiming score parity.
                    if (parity['max_score_difference']>.02 and slug!='qwen-4b') or parity['decision_changes']>1:
                        raise RuntimeError('Batch parity needs investigation')
                    result['parity']=parity
                    tuning.append(dict(parameter=value,**result))
            except Exception as exc:
                write(directory/f'failed-p{value}.json',dict(error=str(exc),created_utc=now()))
        successes=[r for r in tuning if r['errors']==0]
        if not successes:raise RuntimeError('No valid configuration: '+slug)
        selected=max(successes,key=lambda r:r['requests_per_second'])
        write(directory/'freeze.json',dict(created_utc=now(),parameter=selected['parameter'],tuning=tuning,
            criterion='highest valid tuning requests/sec, no errors',measurement_input_hash=reg['inputs']['measure']))
    selected=read(directory/'freeze.json');value=selected['parameter']
    for cache in ([False,True] if spec['backend']=='vllm' else [False]):
        with server(state,slug,value,cache):
            client=Client(state,slug)
            for repeat in range(3):
                # Cycle condition order to reduce systematic warm-runtime order effects.
                cs=[1,32] if cache else [1,8,32,64]
                cs=cs[repeat%len(cs):]+cs[:repeat%len(cs)]
                for concurrency in cs:
                    output=directory/f'measure-cache{int(cache)}-c{concurrency}-r{repeat}'
                    if output.with_suffix('.json').exists():continue
                    client.run(measure,concurrency,output,seed=100+repeat,cache=cache)
    write(directory/'complete.json',dict(created_utc=now(),parameter=value))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--model',required=True)
    a=p.parse_args()
    lock=(Path(a.state)/'.controller.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def stop(signum,frame):raise KeyboardInterrupt('Bounded serving deadline')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop)
    signal.alarm(5*3600)
    if a.model=='all':
        for slug in ['shieldstral','qwen-4b','wildguard','policylm','liquid','kev','clef']:
            if slug not in read(Path(a.state)/'registration.json')['models']:continue
            try:run(a.state,slug)
            except Exception as exc:
                write(Path(a.state)/slug/'failed.json',dict(error=str(exc),created_utc=now()))
                print(slug+' FAILED: '+str(exc),flush=True)
        print('ALL_ATTEMPTED',flush=True)
    else:run(a.state,a.model)
