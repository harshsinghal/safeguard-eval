set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
python3 -m pip install uv
uv venv --python 3.12 /root/correctionenv
uv pip install --python /root/correctionenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/correctionenv/bin/python transformers==5.10.2 accelerate safetensors numpy scipy scikit-learn threadpoolctl pillow mistral-common
uv pip freeze --python /root/correctionenv/bin/python > /root/correction-freeze.txt
nvidia-smi > /root/gpu-environment.txt
cd /root/safeguard-eval
/root/correctionenv/bin/python -m evals.policy_corrections.infer --state /root/correction-state --model shieldstral --stage discovery-validation > /root/shield-development.log 2>&1
printf SHIELD_DEVELOPMENT_COMPLETE
