set -eu
cp /root/modernbert.log /root/modernbert-first-failure.log
cd /root/safeguard-eval
/root/featureenv/bin/python -m evals.contrastive_heads.extract --state /root/contrastive-state --backend modernbert > /root/modernbert.log 2>&1
/root/featureenv/bin/python -m evals.contrastive_heads.extract --state /root/contrastive-state --backend policylm > /root/policylm.log 2>&1
touch /root/CONTRASTIVE_FEATURES_COMPLETE
