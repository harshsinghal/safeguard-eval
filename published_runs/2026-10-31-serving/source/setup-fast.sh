set -eu
uv venv --python 3.12 /root/kevenvfast
uv pip install --python /root/kevenvfast/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/kevenvfast/bin/python transformers==5.17.0 peft==0.21.2 accelerate safetensors numpy scipy scikit-learn fastapi uvicorn flash-linear-attention==0.5.2
uv pip install --python /root/kevenvfast/bin/python --no-deps 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0%2Bcu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl'
uv venv --python 3.12 /root/clefenvfast
uv pip install --python /root/clefenvfast/bin/python torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/clefenvfast/bin/python transformers==5.10.2 accelerate safetensors numpy scipy scikit-learn pillow fastapi uvicorn flash-linear-attention==0.6.0
mkdir -p /root/serving-fast-state/runtime
for task_env in kevenvfast clefenvfast; do
 uv pip freeze --python /root/$task_env/bin/python > /root/serving-fast-state/runtime/$task_env-freeze.txt
done
printf 'FAST_SETUP_COMPLETE\n'
