set -e
cd /root/safeguard-eval
/root/policyenv/bin/python /root/job.py policylm /root/models/policylm b3b2cd408a08a68ab6a30c1fc1e440204e44d57e > /root/policylm.log 2>&1
for adapter in shieldstral cope safeguard; do
 case "$adapter" in
 shieldstral) model=mistralai/Shieldstral-1.0-3B; revision=003ec7e2b0bab5f0e6307edbaf186fa5822b76f5; extra='' ;;
 cope) model=zentropi-ai/cope-b-a4b; revision=b28a1c734eff80d82e5df7964c7dfd0de8509900; extra='' ;;
 safeguard) model=openai/gpt-oss-safeguard-20b; revision=8a11e17b25c973a24099d4016bf2e17dd7ec1574; extra='--reasoning-parser openai_gptoss --attention-backend TRITON_ATTN' ;;
 esac
 export CUDA_HOME=/root/vllmenv/lib/python3.10/site-packages/nvidia/cu13
 /root/vllmenv/bin/vllm serve "$model" --revision "$revision" --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 16384 --gpu-memory-utilization .85 --max-num-seqs 4 --enforce-eager $extra > "/root/$adapter-server.log" 2>&1 &
 server_pid=$!
 trap 'kill "$server_pid" 2>/dev/null || true' EXIT
 /root/vllmenv/bin/python /root/job.py "$adapter" "$model" "$revision" > "/root/$adapter.log" 2>&1
 kill "$server_pid"
 wait "$server_pid" || true
 trap - EXIT
 sleep 5
done
printf '\nALL MODELS COMPLETE\n'
