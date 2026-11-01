"""Complete the cached load curve using already frozen serving configurations."""
import argparse
import fcntl
from pathlib import Path
import signal
from evals.ensemble.common import read,rows,write,now
from .client import Client
from .study import server


def run(state):
    state=Path(state)
    lock=(state/'.controller.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for slug in ['shieldstral','qwen-4b','wildguard']:
        directory=state/slug
        if not (directory/'complete.json').exists():continue
        parameter=read(directory/'freeze.json')['parameter']
        with server(state,slug,parameter,cache=True):
            client=Client(state,slug)
            for repeat in range(3):
                for concurrency in ([8,64] if repeat%2==0 else [64,8]):
                    output=directory/f'measure-cache1-c{concurrency}-r{repeat}'
                    if output.with_suffix('.json').exists():continue
                    client.run(rows(state/'inputs/measure.jsonl'),concurrency,output,seed=100+repeat,cache=True)
        write(directory/'cached-curve-complete.json',dict(created_utc=now(),parameter=parameter,
            additional_concurrency=[8,64],note='No retuning; fills the frozen cached throughput/latency curve'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);a=p.parse_args()
    def stop(signum,frame):raise KeyboardInterrupt('Serving extension deadline')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.alarm(3600)
    run(a.state)
