set -eu
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
python3 -m pip install uv
uv venv --python 3.12 /root/liquidenv
uv pip install --python /root/liquidenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/liquidenv/bin/python transformers==5.12.0 accelerate safetensors numpy scipy scikit-learn
uv pip freeze --python /root/liquidenv/bin/python > /root/liquid-freeze.txt
nvidia-smi > /root/gpu-environment.txt
cd /root/safeguard-eval
/root/liquidenv/bin/python -m evals.liquid_finetune.runner smoke --state /root/liquid-state > /root/smoke.log 2>&1
/root/liquidenv/bin/python -m evals.liquid_finetune.runner extract --state /root/liquid-state > /root/extract.log 2>&1
for rate in 0.00002 0.00005; do
 for seed in 20261031 20261101 20261102; do
  /root/liquidenv/bin/python -m evals.liquid_finetune.runner train --state /root/liquid-state --rate "$rate" --seed "$seed" >> /root/train.log 2>&1
 done
done
touch /root/LIQUID_TRAINING_COMPLETE
