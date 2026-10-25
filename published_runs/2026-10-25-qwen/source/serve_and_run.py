"""Sequential pinned Qwen serving. Explicit phases; inference outputs are immutable."""
import argparse,json,os,subprocess,time,urllib.request,signal
from pathlib import Path
ROOT=Path('/root/safeguard-eval')
p=argparse.ArgumentParser();p.add_argument('--jobs',required=True);a=p.parse_args()
jobs=json.loads(Path(a.jobs).read_text());env=os.environ.copy()
env.update(CUDA_HOME='/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13',HF_HUB_OFFLINE='1')
for model in dict.fromkeys(j['model'] for j in jobs):
    marker=Path('/root')/(model.split('/')[-1]+'.ready.json');server=None
    try:
        for _ in range(600):
            if marker.exists():break
            time.sleep(2)
        else:raise RuntimeError('Checkpoint download timeout')
        ready=json.loads(marker.read_text())
        if any(j['revision']!=ready['revision'] for j in jobs if j['model']==model):raise ValueError('Checkpoint revision mismatch')
        cmd=['/root/vllmenv/bin/vllm','serve',ready['path'],'--served-model-name',model,
             '--host','127.0.0.1','--port','8000','--dtype','bfloat16','--max-model-len','32768',
             '--gpu-memory-utilization','.90','--max-num-seqs','32','--enforce-eager',
             '--limit-mm-per-prompt','{"image":0,"video":0}']
        logfile=Path('/root')/(Path(a.jobs).stem+'-'+model.split('/')[-1]+'-server.log')
        log=logfile.open('w');server=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        print('SERVER',model,server.pid,flush=True)
        for _ in range(240):
            if server.poll() is not None:raise RuntimeError('Server exited; inspect '+str(logfile))
            try:urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2).close();break
            except Exception:time.sleep(3)
        else:raise RuntimeError('Server startup timeout')
        for j in [j for j in jobs if j['model']==model]:
            cmd=['/root/vllmenv/bin/python','-m','evals.qwen_policy.run','--model',model,'--revision',j['revision'],
                 '--policy',j['policy'],'--data',j['data'],'--stage',j['stage'],'--out',str(ROOT/'results/qwen-policy'/j['id'])]
            if j.get('freeze'):cmd+=['--freeze',j['freeze']]
            print('START',j['id'],flush=True);subprocess.run(cmd,cwd=ROOT,env=env,check=True);print('DONE',j['id'],flush=True)
    finally:
        if server:
            try:os.killpg(server.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:server.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid,signal.SIGKILL);server.wait()
            log.close();time.sleep(2)
print('PHASE COMPLETE',a.jobs,flush=True)
