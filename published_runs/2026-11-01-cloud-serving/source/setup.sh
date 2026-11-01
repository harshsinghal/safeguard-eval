set -eu
mkdir -p /root/cloud-state/runtime
nvidia-smi > /root/cloud-state/runtime/gpu-environment.txt
lscpu > /root/cloud-state/runtime/cpu-environment.txt
apt-get update -qq
apt-get install -y -qq build-essential ninja-build g++-12 > /root/compiler-setup.log 2>&1
python3 -m pip install uv
uv venv --python 3.12 /root/vllmenv
uv pip install --python /root/vllmenv/bin/python 'vllm==0.32.0' 'transformers==5.17.0' httpx numpy
uv pip install --python /root/vllmenv/bin/python nvidia-cuda-nvcc==13.0.88 nvidia-cuda-crt==13.0.88 nvidia-nvvm==13.0.88
ln -sfn lib /root/vllmenv/lib/python3.12/site-packages/nvidia/cu13/lib64
ln -sfn libcudart.so.13 /root/vllmenv/lib/python3.12/site-packages/nvidia/cu13/lib/libcudart.so
uv pip freeze --python /root/vllmenv/bin/python > /root/cloud-state/runtime/vllm-freeze.txt
uv venv --python 3.12 /root/sglangenv
uv pip install --python /root/sglangenv/bin/python --prerelease=allow 'sglang==0.5.23'
printf '/root/sglangenv/bin/python\n' > /root/cloud-state/runtime/sglang-python.txt
uv pip freeze --python /root/sglangenv/bin/python > /root/cloud-state/runtime/sglang-freeze.txt
/root/sglangenv/bin/python -c 'import torch,sglang; print(torch.__version__,torch.version.cuda,torch.cuda.is_available(),sglang.__version__)' > /root/cloud-state/runtime/sglang-versions.txt
cd /root/safeguard-eval
/root/vllmenv/bin/python -m evals.serving.cloud_lengths --state /root/cloud-state --action prepare
printf 'SETUP_COMPLETE\n'
