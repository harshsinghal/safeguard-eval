set -eu
until grep -q '^LONG_CONTROL_ATTEMPTED$' /root/cloud-state/long-control-controller.log; do sleep 5; done
mkdir -p /root/cloud-shield-hf/runtime
cp /root/cloud-state/runtime/sglang-python.txt /root/cloud-shield-hf/runtime/sglang-python.txt
/root/vllmenv/bin/python /root/prepare-shield-hf.py
cd /root/safeguard-eval
/root/vllmenv/bin/python -m evals.serving.cloud_shield_smoke --state /root/cloud-shield-hf
printf 'HF_CANARY_ATTEMPTED\n'
