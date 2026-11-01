set -eu
apt-get update -qq
apt-get install -y -qq build-essential ninja-build python3-dev g++-12 > /root/compiler-setup.log 2>&1
python3 -m pip install uv
uv venv --python 3.12 /root/vllmenv
uv pip install --python /root/vllmenv/bin/python 'vllm==0.32.0' 'transformers==5.17.0' 'sentencepiece==0.2.2' 'protobuf==7.36.2'
uv pip install --python /root/vllmenv/bin/python nvidia-cuda-nvcc==13.0.88 nvidia-cuda-crt==13.0.88 nvidia-nvvm==13.0.88
ln -sfn lib /root/vllmenv/lib/python3.12/site-packages/nvidia/cu13/lib64
ln -sfn libcudart.so.13 /root/vllmenv/lib/python3.12/site-packages/nvidia/cu13/lib/libcudart.so
uv venv --python 3.12 /root/policyenv
uv pip install --python /root/policyenv/bin/python torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/policyenv/bin/python transformers==4.57.6 huggingface_hub==0.36.2 safetensors numpy scipy scikit-learn fastapi uvicorn
uv venv --python 3.12 /root/kevenv
uv pip install --python /root/kevenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/kevenv/bin/python transformers==5.17.0 peft==0.21.2 accelerate safetensors numpy scipy scikit-learn fastapi uvicorn
uv venv --python 3.12 /root/clefenv
uv pip install --python /root/clefenv/bin/python torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/clefenv/bin/python transformers==5.10.2 accelerate safetensors numpy scipy scikit-learn pillow fastapi uvicorn
uv venv --python 3.12 /root/liquidenv
uv pip install --python /root/liquidenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/liquidenv/bin/python transformers==5.12.0 accelerate safetensors numpy scipy scikit-learn fastapi uvicorn
mkdir -p /root/serving-state/runtime
for task_env in vllmenv policyenv kevenv clefenv liquidenv; do
 uv pip freeze --python /root/$task_env/bin/python > /root/serving-state/runtime/$task_env-freeze.txt
done
nvidia-smi > /root/serving-state/runtime/gpu-environment.txt
lscpu > /root/serving-state/runtime/cpu-environment.txt
df -h > /root/serving-state/runtime/disk.txt
printf 'SETUP_COMPLETE\n'
