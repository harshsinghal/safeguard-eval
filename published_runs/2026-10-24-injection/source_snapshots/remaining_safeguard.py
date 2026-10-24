"""Continue unrun Safeguard splits after a completed split reports errors; never retry a case."""
import sys,json,time,urllib.request
from pathlib import Path
sys.path.insert(0,'/root/safeguard-eval')
from evals.run import main
for _ in range(180):
 try:urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=5).close();break
 except Exception:time.sleep(5)
else:raise SystemExit('Server unavailable')
common=['--adapter','safeguard','--model','openai/gpt-oss-safeguard-20b','--max-tokens','8192','--deployment-note','GPU.ai RTX PRO 6000 Blackwell 96GB; revision 8a11e17b25c973a24099d4016bf2e17dd7ec1574; native PolicyLM BF16 or vLLM 0.31.0 BF16 (Safeguard MXFP4), eager; see environment.txt','--base-url','http://127.0.0.1:8000/v1','--api-key-env','LOCAL_MODEL_KEY']
for track,policy,split in [('deepset','binary-policy','test'),('challenge','policy','dev'),('challenge','policy','test')]:
 out=Path(f'results/safeguard-{track}-{split}')
 if out.exists():
  assert (out/'summary.json').exists(),'Do not overwrite incomplete run'
  print('Already completed:',out,flush=True);continue
 rc=main(common+['--data',f'evals/injection/{track}.jsonl','--policy',f'evals/injection/{policy}.json','--split',split,'--out',str(out)])
 print('Split completed, error status:',rc,flush=True)
print('ALL SAFEGUARD SPLITS COMPLETE',flush=True)
