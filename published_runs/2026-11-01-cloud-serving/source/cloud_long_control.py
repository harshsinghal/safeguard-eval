"""Exploratory fixed alternative chunk size; never replaces primary selection."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import signal
from evals.serving.cloud_lengths import server,Client,rows,write


def run(state):
    reg=json.loads((state/'registration.json').read_text())
    freeze=json.loads((state/'input-freeze.json').read_text())
    assert hashlib.sha256((state/'private-inputs/4096.jsonl').read_bytes()).hexdigest()==freeze['input_files']['4096.jsonl']
    data=rows(state/'private-inputs/4096.jsonl')
    assert len(data)==64
    for engine in ('vllm','sglang'):
        out=state/'long-input-control'/engine;out.mkdir(parents=True,exist_ok=True)
        try:
            with server(state,engine,8192):
                client=Client(reg['model']['model'])
                for repeat in (0,1):
                    for concurrency in ([1,8] if repeat==0 else [8,1]):
                        with ThreadPoolExecutor(max_workers=concurrency) as pool:
                            list(pool.map(client.one,data[:8]))
                        client.run(data,concurrency,out/f'measure-4096-c{concurrency}-r{repeat}',100+repeat)
            write(out/'complete.json',dict(parameter=8192,scope='exploratory control; no primary reselection'))
        except Exception as exc:
            write(out/'failed.json',dict(error=str(exc)))


if __name__=='__main__':
    def stop(signum,frame): raise KeyboardInterrupt('Bounded control deadline')
    signal.signal(signal.SIGTERM,stop)
    p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True)
    run(p.parse_args().state)
