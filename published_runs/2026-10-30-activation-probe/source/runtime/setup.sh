set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
python3 -m pip install uv
uv venv --python 3.12 /root/policyenv
uv pip install --python /root/policyenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/policyenv/bin/python transformers==4.57.6 'huggingface_hub<1' accelerate safetensors numpy scipy scikit-learn
uv venv --python 3.12 /root/qwenenv
uv pip install --python /root/qwenenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/qwenenv/bin/python transformers==5.10.2 accelerate safetensors numpy scipy scikit-learn pillow
uv pip freeze --python /root/policyenv/bin/python > /root/policy-freeze.txt
uv pip freeze --python /root/qwenenv/bin/python > /root/qwen-freeze.txt
nvidia-smi > /root/gpu-environment.txt
cd /root/safeguard-eval
/root/policyenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model policylm --stage development > /root/policylm-development.log 2>&1
/root/qwenenv/bin/python -m evals.activation_probe.extract --state /root/probe-state --model qwen --stage development > /root/qwen-development.log 2>&1
echo DEVELOPMENT_COMPLETE
