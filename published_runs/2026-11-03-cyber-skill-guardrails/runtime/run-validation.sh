set -eu
cd /root/safeguard-eval
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_PROGRESS_BARS=1
/root/policyenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug promptguard --split validation --vendor /root/decision-vendor > /root/promptguard-validation.log 2>&1
/root/llamaenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug llamaguard --split validation --vendor /root/decision-vendor > /root/llamaguard-validation.log 2>&1
/root/policyenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug policylm --split validation --vendor /root/decision-vendor > /root/policylm-validation.log 2>&1
/root/clefenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug shieldstral --split validation --vendor /root/decision-vendor > /root/shieldstral-validation.log 2>&1
/root/kevenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug qwen --split validation --vendor /root/decision-vendor > /root/qwen-validation.log 2>&1
/root/kevenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug kev --split validation --vendor /root/decision-vendor > /root/kev-validation.log 2>&1
/root/clefenv/bin/python -m evals.cyber_skill_guardrails.infer --state /root/cyber-skill-state --slug clef --split validation --vendor /root/decision-vendor > /root/clef-validation.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.embeddings --state /root/cyber-skill-state --split development > /root/jina-validation.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.heads --state /root/cyber-skill-state --slug jina-v2 --split validation > /root/jina-v2-heads-validation.log 2>&1
/root/jinaenv/bin/python -m evals.cyber_skill_guardrails.heads --state /root/cyber-skill-state --slug jina-v2-md --split validation > /root/jina-v2-md-heads-validation.log 2>&1
touch /root/validation-complete
