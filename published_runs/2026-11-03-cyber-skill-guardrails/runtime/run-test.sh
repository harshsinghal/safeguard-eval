set -eu
cd /root/safeguard-eval
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_PROGRESS_BARS=1
/root/policyenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug promptguard --split test --vendor /root/decision-vendor > /root/promptguard-test.log 2>&1
/root/llamaenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug llamaguard --split test --vendor /root/decision-vendor > /root/llamaguard-test.log 2>&1
/root/policyenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug policylm --split test --vendor /root/decision-vendor > /root/policylm-test.log 2>&1
/root/clefenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug shieldstral --split test --vendor /root/decision-vendor > /root/shieldstral-test.log 2>&1
/root/kevenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug qwen --split test --vendor /root/decision-vendor > /root/qwen-test.log 2>&1
/root/kevenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug kev --split test --vendor /root/decision-vendor > /root/kev-test.log 2>&1
/root/clefenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug clef --split test --vendor /root/decision-vendor > /root/clef-test.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.embeddings --state /root/cyber-skill-state --split test > /root/jina-test.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.heads --state /root/cyber-skill-state --slug jina-v2 --split test > /root/jina-v2-heads-test.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.heads --state /root/cyber-skill-state --slug jina-v2-md --split test > /root/jina-v2-md-heads-test.log 2>&1
touch /root/test-complete
