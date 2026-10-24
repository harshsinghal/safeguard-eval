set -e
while pgrep -f '^/root/vllmenv/bin/python /root/job.py safeguard ' >/dev/null; do sleep 5; done
cd /root/safeguard-eval
if test -f results/safeguard-challenge-test/summary.json; then exit 0; fi
# Original shell tears down the server when the job returns nonzero.
sleep 10
export CUDA_HOME=/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13
/root/vllmenv/bin/vllm serve openai/gpt-oss-safeguard-20b --revision 8a11e17b25c973a24099d4016bf2e17dd7ec1574 --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 16384 --gpu-memory-utilization .85 --max-num-seqs 4 --enforce-eager --reasoning-parser openai_gptoss --attention-backend TRITON_ATTN > /root/safeguard-continuation-server.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
/root/vllmenv/bin/python /root/remaining_safeguard.py > /root/safeguard-continuation.log 2>&1
