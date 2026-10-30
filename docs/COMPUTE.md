# Compute for future experiments

Use **GPU.ai first**, with **Runpod as the fallback** when GPU.ai credits are exhausted or the required GPU capacity is unavailable. The project owner has provided Runpod API credentials in a suitably named file under `~/workspace/KEYS`; read credentials locally when needed and keep their values out of source control, logs, and published artifacts.

Before provisioning, check the available GPU memory, current hourly rate, expected runtime, and remaining approved budget. Spending across GPU and API providers counts toward the same budget. On October 25, 2026 the user raised the cumulative cap to **$20**. Switching providers does not reset or increase that cap.

Provision on demand, set a spending/runtime cutoff, collect artifacts during execution, and terminate resources after the run. Record the provider, GPU, software environment, runtime, billing, and termination evidence with each experiment.

The latest paid run, the [frozen-representation ledger](../published_runs/2026-10-30-activation-probe/billing.json), records **$14.17540555656 cumulative spend**, leaving **$5.82459444344** within the $20 cap. It cost **$0.38** on GPU.ai (2,098 billed GPU-seconds at $0.65/hour), including setup and development failures. The instance was terminated and temporary SSH keys removed. RunPod was not used.

The earlier [Kev/Clef ledger](../published_runs/2026-10-29-decision-models/billing.json) recorded $13.79540555656 cumulatively. The [decision-score ensemble](decision-ensemble/README.md) added $0 in GPU/API charges using cached scores on local CPU. Other studies are recorded in the [HateXplain ledger](hatexplain/progress.json), [Qwen ledger](qwen-policy/progress.json), [frontier API ledger](frontier-api/progress.json), and [policy-transfer ledger](policy-transfer/progress.json). Consult the latest ledger before starting new paid work. This provider preference does not reserve a GPU or start an experiment.
