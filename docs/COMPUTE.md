# Compute for future experiments

Use **GPU.ai first**, with **Runpod as the fallback** when GPU.ai credits are exhausted or the required GPU capacity is unavailable. The project owner has provided Runpod API credentials in a suitably named file under `~/workspace/KEYS`; read credentials locally when needed and keep their values out of source control, logs, and published artifacts.

Before provisioning, check the available GPU memory, current hourly rate, expected runtime, and remaining approved budget. Spending across GPU and API providers counts toward the same budget. On October 25, 2026 the user raised the cumulative cap to **$20**. Switching providers does not reset or increase that cap.

Provision on demand, set a spending/runtime cutoff, collect artifacts during execution, and terminate resources after the run. Record the provider, GPU, software environment, runtime, billing, and termination evidence with each experiment.

The latest paid run, the [smart-ensemble ledger](../published_runs/2026-10-31-smart-ensemble/billing.json), records **$16.69001787256 cumulative accounted spend**, leaving **$3.30998212744** within the $20 cap. New cost was **$1.424612316**: $0.54 on GPU.ai (2,447 billed GPU-seconds at $0.80/hour), $0.873602268 in reported Jev API charges, and $0.011010048 conservatively accounted for four unknown-cost transport failures. Those failure allowances are upper bounds, not exact billed amounts. The L40S was terminated, billing reconciled and temporary local/provider SSH keys removed. RunPod was not needed. The run reserved at most $2.40 for a three-hour GPU and $1 for API calls; local fitting and reproduction made no inference calls.

The preceding [training-error policy-correction ledger](../published_runs/2026-10-30-policy-corrections/billing.json) recorded **$15.26540555656 cumulative spend** after a **$0.72** GPU.ai run (3,229 billed GPU-seconds). Its L40S instance was also terminated and temporary SSH keys removed.

The preceding [Shieldstral representation ledger](../published_runs/2026-10-30-shield-probe/billing.json) recorded $14.54540555656 cumulatively after a $0.37 run. The [PolicyLM representation ledger](../published_runs/2026-10-30-activation-probe/billing.json) recorded $14.17540555656 cumulatively after a $0.38 run. Both earlier instances were also terminated.

The earlier [Kev/Clef ledger](../published_runs/2026-10-29-decision-models/billing.json) recorded $13.79540555656 cumulatively. The [decision-score ensemble](decision-ensemble/README.md) added $0 in GPU/API charges using cached scores on local CPU. Other studies are recorded in the [HateXplain ledger](hatexplain/progress.json), [Qwen ledger](qwen-policy/progress.json), [frontier API ledger](frontier-api/progress.json), and [policy-transfer ledger](policy-transfer/progress.json). Consult the latest ledger before starting new paid work. This provider preference does not reserve a GPU or start an experiment.
