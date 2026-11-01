set -eu
until grep -q '^REPAIR_ATTEMPTED$' /root/cloud-repair-controller.log; do sleep 5; done
cd /root/safeguard-eval
/root/vllmenv/bin/python -m evals.serving.cloud_long_control --state /root/cloud-state
printf 'LONG_CONTROL_ATTEMPTED\n'
