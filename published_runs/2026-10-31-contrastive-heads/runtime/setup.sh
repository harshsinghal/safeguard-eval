set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
python3 -m pip install uv
uv venv --python 3.12 /root/featureenv
uv pip install --python /root/featureenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/featureenv/bin/python transformers==4.57.6 'huggingface_hub<1' accelerate safetensors numpy scipy scikit-learn
uv pip freeze --python /root/featureenv/bin/python > /root/feature-freeze.txt
nvidia-smi > /root/gpu-environment.txt
cd /root/safeguard-eval
/root/featureenv/bin/python -m evals.contrastive_heads.extract --state /root/contrastive-state --backend modernbert > /root/modernbert.log 2>&1
/root/featureenv/bin/python -m evals.contrastive_heads.extract --state /root/contrastive-state --backend policylm > /root/policylm.log 2>&1
touch /root/CONTRASTIVE_FEATURES_COMPLETE
