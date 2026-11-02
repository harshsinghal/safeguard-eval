set -eu
cd /root/safeguard-eval
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
/root/policyenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug policylm --split validation --vendor /root/decision-vendor > /root/policylm-validation.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug shieldstral --split validation --vendor /root/decision-vendor > /root/shieldstral-validation.log 2>&1
/root/kevenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug kev --split validation --vendor /root/decision-vendor > /root/kev-validation.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug clef --split validation --vendor /root/decision-vendor > /root/clef-validation.log 2>&1
touch /root/validation-native-complete
