set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
cd /root/safeguard-eval
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model shieldstral --stage development > /root/shieldstral-development.log 2>&1
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model qwen --stage development > /root/qwen-development.log 2>&1
