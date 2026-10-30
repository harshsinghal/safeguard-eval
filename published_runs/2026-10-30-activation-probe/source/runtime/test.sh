set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
cd /root/safeguard-eval
/root/policyenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model policylm --stage test > /root/policylm-test.log 2>&1
/root/qwenenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model qwen --stage test > /root/qwen-test.log 2>&1
echo TEST_EXTRACTION_COMPLETE
