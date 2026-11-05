set -eu
test -f /root/watchdog-ready.json
python3 -m pip install --break-system-packages uv
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
uv venv --python 3.12 /root/kevenv
uv pip install --python /root/kevenv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/kevenv/bin/python transformers==5.17.0 peft==0.21.2 accelerate safetensors numpy==2.5.4 scipy==1.18.1 scikit-learn==1.9.1 pillow flash-linear-attention==0.5.2 pydantic==2.12.5
uv pip install --python /root/kevenv/bin/python --no-deps 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0%2Bcu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl'
uv venv --python 3.12 /root/policyenv
uv pip install --python /root/policyenv/bin/python torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/policyenv/bin/python transformers==4.57.6 huggingface_hub==0.36.2 einops safetensors numpy==2.5.4 scipy==1.18.1 scikit-learn==1.9.1
uv venv --python 3.12 /root/clefenv
uv pip install --python /root/clefenv/bin/python torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /root/clefenv/bin/python transformers==5.10.2 accelerate safetensors numpy==2.5.4 scipy==1.18.1 scikit-learn==1.9.1 pillow
apt-get update -qq
apt-get install -y -qq build-essential python3-dev ninja-build rsync > /root/apt.log 2>&1
uv venv --python 3.10 /root/vllmenv
uv pip install --python /root/vllmenv/bin/python vllm==0.31.0 numpy scipy scikit-learn
mkdir -p /root/stepguard-state/runtime
for env in kevenv policyenv clefenv vllmenv; do
 uv pip freeze --python /root/$env/bin/python > /root/stepguard-state/runtime/$env-freeze.txt
done
nvidia-smi > /root/stepguard-state/runtime/gpu-environment.txt
touch /root/setup-complete
bash /root/run-stage.sh validation
