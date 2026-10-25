set -e
apt-get update -qq
apt-get install -y -qq build-essential python3-dev ninja-build > /root/apt.log 2>&1
python3 -m pip install uv
uv venv --python 3.10 /root/vllmenv
uv pip install --python /root/vllmenv/bin/python 'vllm==0.31.0' 'sentencepiece==0.2.2' 'protobuf==7.36.2'
uv pip freeze --python /root/vllmenv/bin/python > /root/vllm-freeze.txt
nvidia-smi > /root/environment.txt
nohup /root/vllmenv/bin/python /root/prefetch.py > /root/prefetch.log 2>&1 < /dev/null &
python3 /root/serve_and_run.py --jobs /root/pilot-jobs.json
