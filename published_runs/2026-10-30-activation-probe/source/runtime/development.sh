set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
cd /root/safeguard-eval
/root/policyenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model policylm --stage development > /root/policylm-development.log 2>&1
/root/qwenenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model qwen --stage development > /root/qwen-development.log 2>&1
echo DEVELOPMENT_COMPLETE
