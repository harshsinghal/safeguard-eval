set -eu
while kill -0 14706 2>/dev/null; do sleep 5; done
cd /root
cp /root/study.log /root/serving-state/runtime/tokenizer-attempt-controller.log
mv /root/serving-state/wildguard /root/serving-state/runtime/wildguard-tokenizer-attempt
mkdir /root/serving-state/wildguard
tar xzf tokenizer-repair-source.tar.gz
uv pip install --python /root/policyenv/bin/python httpx==0.28.1 sentencepiece==0.2.2 protobuf==7.36.2 > /root/tokenizer-setup.log 2>&1
uv pip freeze --python /root/policyenv/bin/python > /root/serving-state/runtime/wildguard-client-freeze.txt
cd /root/safeguard-eval
PYTHONPATH=/root/safeguard-eval /root/vllmenv/bin/python /root/tokenizer-check.py
PYTHONPATH=/root/safeguard-eval /root/policyenv/bin/python /root/tokenizer-check.py
/root/policyenv/bin/python -m evals.serving.study --state /root/serving-state --model all > /root/study.log 2>&1
mkdir -p /root/serving-fast-state/runtime-reference
cp -r /root/serving-state/inputs /root/serving-fast-state/inputs
cp -r /root/serving-state/policies /root/serving-fast-state/policies
for task_model in kev clef; do
 cp /root/serving-state/$task_model/parity-p8.jsonl /root/serving-fast-state/runtime-reference/$task_model.jsonl
done
/root/vllmenv/bin/python -m evals.serving.study --state /root/serving-fast-state --model all > /root/fast-study.log 2>&1
cd /root
tar xzf phase3-source.tar.gz
mkdir -p /root/serving-policy-state/runtime-reference
cp -r /root/serving-state/inputs /root/serving-policy-state/inputs
cp -r /root/serving-state/policies /root/serving-policy-state/policies
cp /root/serving-state/policylm/parity-p8.jsonl /root/serving-policy-state/runtime-reference/policylm.jsonl
cd /root/safeguard-eval
/root/vllmenv/bin/python -m evals.serving.study --state /root/serving-policy-state --model all > /root/policy-study.log 2>&1
/root/policyenv/bin/python -m evals.serving.cached_sweep --state /root/serving-state > /root/cached-study.log 2>&1
printf 'ALL_STAGES_FINISHED\n'
