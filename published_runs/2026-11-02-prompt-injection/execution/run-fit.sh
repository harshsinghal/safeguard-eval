set -eu
cd /root/safeguard-eval
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
/root/policyenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug policylm --split fit --vendor /root/decision-vendor > /root/policylm-fit.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug shieldstral --split fit --vendor /root/decision-vendor > /root/shieldstral-fit.log 2>&1
/root/kevenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug kev --split fit --vendor /root/decision-vendor > /root/kev-fit.log 2>&1
/root/clefenv/bin/python -m evals.prompt_injection.infer --state /root/injection-state --slug clef --split fit --vendor /root/decision-vendor > /root/clef-fit.log 2>&1
touch /root/fit-native-complete
