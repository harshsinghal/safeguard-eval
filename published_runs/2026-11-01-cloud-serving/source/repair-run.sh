set -u
until grep -q '^SHIELD_ATTEMPTED$' /root/cloud-shield-controller.log; do sleep 5; done
mv /root/cloud-state/sglang /root/cloud-state/sglang-initial-failed
mv /root/cloud-state/sglang-controller.log /root/cloud-state/sglang-initial-failed/controller.log
mv /root/cloud-shield /root/cloud-shield-initial
mkdir -p /root/cloud-shield/runtime
cp /root/cloud-shield-initial/registration.json /root/cloud-shield/registration.json
cp /root/cloud-shield-initial/policy.json /root/cloud-shield/policy.json
cp /root/cloud-shield-initial/private-fit.jsonl /root/cloud-shield/private-fit.jsonl
cp /root/cloud-state/runtime/sglang-python.txt /root/cloud-shield/runtime/sglang-python.txt
cp /root/cloud-state/runtime-amendment.json /root/cloud-shield/runtime-amendment.json
cd /root/safeguard-eval
/root/vllmenv/bin/python -m evals.serving.cloud_lengths --state /root/cloud-state --action sglang > /root/cloud-state/sglang-controller.log 2>&1
printf 'Repaired SGLang exit: %s\n' "$?"
/root/vllmenv/bin/python -m evals.serving.cloud_shield_smoke --state /root/cloud-shield > /root/cloud-shield/repaired-controller.log 2>&1
printf 'Repaired Shield exit: %s\n' "$?"
printf 'REPAIR_ATTEMPTED\n'
