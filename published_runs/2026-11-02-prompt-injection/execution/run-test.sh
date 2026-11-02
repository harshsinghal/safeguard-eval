set -eu
cd /root/safeguard-eval
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
/root/policyenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug policylm --split test --vendor /root/decision-vendor > /root/policylm-test.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug shieldstral --split test --vendor /root/decision-vendor > /root/shieldstral-test.log 2>&1
/root/kevenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug kev --split test --vendor /root/decision-vendor > /root/kev-test.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug clef --split test --vendor /root/decision-vendor > /root/clef-test.log 2>&1
touch /root/test-native-complete
