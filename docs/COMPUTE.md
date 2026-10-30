# Compute for future experiments

Use **GPU.ai first**, with **Runpod as the fallback** when GPU.ai credits are exhausted or the required GPU capacity is unavailable. The project owner has provided Runpod API credentials in a suitably named file under `~/workspace/KEYS`; read credentials locally when needed and keep their values out of source control, logs, and published artifacts.

Before provisioning, check the available GPU memory, current hourly rate, expected runtime, and remaining approved budget. Spending across GPU and API providers counts toward the same budget. On October 25, 2026 the user raised the cumulative cap to **$20**. Switching providers does not reset or increase that cap.

Provision on demand, set a spending/runtime cutoff, collect artifacts during execution, and terminate resources after the run. Record the provider, GPU, software environment, runtime, billing, and termination evidence with each experiment.

The latest paid run, the [training-error policy-correction ledger](../published_runs/2026-10-30-policy-corrections/billing.json), records **$15.26540555656 cumulative spend**, leaving **$4.73459444344** within the $20 cap. It cost **$0.72** on GPU.ai (3,229 billed GPU-seconds at $0.80/hour). The L40S instance was terminated, billing reconciled and temporary local/provider SSH keys removed. RunPod was not used. The run had a three-hour provider auto-termination limit and a $2.40 maximum reservation.

The preceding [Shieldstral representation ledger](../published_runs/2026-10-30-shield-probe/billing.json) recorded $14.54540555656 cumulatively after a $0.37 run. The [PolicyLM representation ledger](../published_runs/2026-10-30-activation-probe/billing.json) recorded $14.17540555656 cumulatively after a $0.38 run. Both earlier instances were also terminated.

The earlier [Kev/Clef ledger](../published_runs/2026-10-29-decision-models/billing.json) recorded $13.79540555656 cumulatively. The [decision-score ensemble](decision-ensemble/README.md) added $0 in GPU/API charges using cached scores on local CPU. Other studies are recorded in the [HateXplain ledger](hatexplain/progress.json), [Qwen ledger](qwen-policy/progress.json), [frontier API ledger](frontier-api/progress.json), and [policy-transfer ledger](policy-transfer/progress.json). Consult the latest ledger before starting new paid work. This provider preference does not reserve a GPU or start an experiment.
