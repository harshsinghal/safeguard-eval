set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
cd /root/safeguard-eval
/root/correctionenv/bin/python -m evals.policy_corrections.infer --state /root/correction-state --model shieldstral --stage final
/root/correctionenv/bin/python -m evals.policy_corrections.infer --state /root/correction-state --model qwen --stage final
touch /root/final-complete
