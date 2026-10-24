"""Remote phase launcher. Explicit adapter/stage/jobs; never opens test without freeze."""
import argparse,json,os,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path('/root/safeguard-eval')
MODELS={'policylm':'musubilabs/policylm-1.7b','wildguard':'allenai/wildguard','shieldstral':'mistralai/Shieldstral-1.0-3B','cope':'zentropi-ai/cope-b-a4b','safeguard':'openai/gpt-oss-safeguard-20b'}
p=argparse.ArgumentParser();p.add_argument('--jobs',required=True);a=p.parse_args()
revs=json.loads((ROOT/'evals/wildguard/revisions.json').read_text())
jobs=json.loads(Path(a.jobs).read_text());env=os.environ.copy();env['CUDA_HOME']='/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13';env['HF_HUB_OFFLINE']='1'
for adapter in dict.fromkeys(j['adapter'] for j in jobs):
 model=MODELS[adapter];revision=revs[model]['revision'];server=None
 try:
  if adapter!='policylm':
   checkpoint='/root/.cache/huggingface/hub/models--'+model.replace('/','--')+'/snapshots/'+revision
   cmd=['/root/vllmenv/bin/vllm','serve',checkpoint,'--served-model-name',model,'--host','127.0.0.1','--port','8000','--dtype','bfloat16','--max-model-len','32768','--gpu-memory-utilization','.88','--max-num-seqs','32','--enforce-eager']
   if adapter=='wildguard':cmd+=['--tokenizer','/root/wildguard-tokenizer']
   if adapter=='safeguard':cmd+=['--reasoning-parser','openai_gptoss','--attention-backend','TRITON_ATTN']
   log=open('/root/'+Path(a.jobs).stem+'-'+adapter+'-server.log','w')
   server=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
   for _ in range(180):
    if server.poll() is not None:raise RuntimeError('Server exited')
    try:urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2).close();break
    except Exception:time.sleep(3)
   else:raise RuntimeError('Server startup timed out')
  for job in [j for j in jobs if j['adapter']==adapter]:
   out=ROOT/'results/wildguard'/job['id']
   if out.exists():raise RuntimeError('Refusing to overwrite '+str(out))
   py='/root/policyenv/bin/python' if adapter in ('policylm','wildguard') else '/root/vllmenv/bin/python'
   cmd=[py,'-m','evals.wildguard.run','--adapter',adapter,'--model','/root/models/policylm' if adapter=='policylm' else model,'--revision',revision,'--data',job['data'],'--stage',job['stage'],'--out',str(out)]
   if adapter!='wildguard':cmd+=['--policy',job['policy']]
   if job.get('freeze'):cmd+=['--freeze',job['freeze']]
   print('START',job['id'],flush=True)
   subprocess.run(cmd,cwd=ROOT,env=env,check=True)
   print('DONE',job['id'],flush=True)
 finally:
  if server:
   server.terminate()
   try:server.wait(timeout=45)
   except subprocess.TimeoutExpired:server.kill();server.wait()
   log.close();time.sleep(3)
print('PHASE COMPLETE',a.jobs,flush=True)
