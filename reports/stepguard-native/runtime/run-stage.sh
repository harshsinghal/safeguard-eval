set -eu
stage=$1
test -f /root/watchdog-ready.json
cd /root/study
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
for model in policylm shieldstral kev clef; do
 case "$model" in
  policylm) runtime=/root/policyenv/bin/python;;
  kev) runtime=/root/kevenv/bin/python;;
  *) runtime=/root/clefenv/bin/python;;
 esac
 "$runtime" -m evals.stepguard.infer --state /root/stepguard-state --model "$model" --split "$stage" --vendor /root/vendor
done
bash /root/run-safeguard.sh "$stage"
touch "/root/$stage-complete"
