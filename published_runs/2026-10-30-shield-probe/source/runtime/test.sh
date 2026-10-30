set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
cd /root/safeguard-eval
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model shieldstral --stage test > /root/shieldstral-test.log 2>&1
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model qwen --stage test > /root/qwen-test.log 2>&1
