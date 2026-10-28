set -e
apt-get update -qq
apt-get install -y -qq build-essential python3-dev ninja-build > /root/apt.log 2>&1
python3 -m pip install uv
uv venv --python 3.10 --system-site-packages /root/policyenv
/root/policyenv/bin/python -c 'import torch' || uv pip install --python /root/policyenv/bin/python torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/policyenv/bin/python 'transformers==4.57.6' 'huggingface_hub==0.36.2' safetensors
uv venv --python 3.10 /root/vllmenv
uv pip install --python /root/vllmenv/bin/python 'vllm==0.31.0' 'sentencepiece==0.2.2' 'protobuf==7.36.2'
uv pip freeze --python /root/policyenv/bin/python > /root/policy-freeze.txt
uv pip freeze --python /root/vllmenv/bin/python > /root/vllm-freeze.txt
nvidia-smi > /root/environment.txt
/root/vllmenv/bin/python /root/prefetch.py
cd /root/safeguard-eval
/root/policyenv/bin/python -m evals.ensemble.infer --state /root/ensemble-state --slug policylm
/root/vllmenv/bin/python -m evals.ensemble.infer --state /root/ensemble-state --slug shieldstral
/root/vllmenv/bin/python -m evals.ensemble.infer --state /root/ensemble-state --slug qwen-4b
printf 'ENSEMBLE_DEVELOPMENT_COMPLETE\n'
