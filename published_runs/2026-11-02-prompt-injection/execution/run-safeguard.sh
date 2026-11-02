set -eu
stage="$1"
case "$stage" in fit|validation|test) ;; *) exit 2 ;; esac
cd /root/safeguard-eval
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export CUDA_HOME=/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13
/root/vllmenv/bin/vllm serve openai/gpt-oss-safeguard-20b --revision 8a11e17b25c973a24099d4016bf2e17dd7ec1574 --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 32768 --gpu-memory-utilization .85 --max-num-seqs 16 --enforce-eager --reasoning-parser openai_gptoss --attention-backend TRITON_ATTN > /root/safeguard-server-$stage.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
/root/vllmenv/bin/python - <<'PY'
import time,urllib.request
for _ in range(180):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2) as r:assert r.status==200
  break
 except Exception:time.sleep(2)
else:raise SystemExit('Server did not become ready')
PY
/root/vllmenv/bin/python -m evals.prompt_injection.local_safeguard --state /root/injection-state --split "$stage" --concurrency 16 > /root/safeguard-$stage.log 2>&1
touch /root/$stage-safeguard-complete
