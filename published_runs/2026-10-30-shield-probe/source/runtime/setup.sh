set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
python3 -m pip install uv
uv venv --python 3.12 /root/probeenv
uv pip install --python /root/probeenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/probeenv/bin/python transformers==5.10.2 accelerate safetensors numpy scipy scikit-learn threadpoolctl pillow mistral-common
uv pip freeze --python /root/probeenv/bin/python > /root/probe-freeze.txt
nvidia-smi > /root/gpu-environment.txt
cd /root/safeguard-eval
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model shieldstral --stage development > /root/shieldstral-development.log 2>&1
/root/probeenv/bin/python -m evals.shield_probe.extract --state /root/probe-state --model qwen --stage development > /root/qwen-development.log 2>&1
printf DEVELOPMENT_COMPLETE
