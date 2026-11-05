set -eu
stage=$1
cd /root/study
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
export CUDA_HOME=/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13
/root/vllmenv/bin/vllm serve openai/gpt-oss-safeguard-20b --revision 8a11e17b25c973a24099d4016bf2e17dd7ec1574 --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 32768 --gpu-memory-utilization .85 --max-num-seqs 64 --enforce-eager --reasoning-parser openai_gptoss --attention-backend TRITON_ATTN > "/root/vllm-$stage.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
/root/vllmenv/bin/python - <<'PY'
import time,urllib.request
for i in range(300):
 try:
  urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).read();break
 except Exception:time.sleep(2)
else:raise RuntimeError('vLLM did not become ready')
PY
/root/vllmenv/bin/python -m evals.stepguard.infer --state /root/stepguard-state --model safeguard --split "$stage" --concurrency 64
