# Compute for future experiments

Use **GPU.ai first**, with **Runpod as the fallback** when GPU.ai credits are exhausted or the required GPU capacity is unavailable. The project owner has provided Runpod API credentials in a suitably named file under `~/workspace/KEYS`; read credentials locally when needed and keep their values out of source control, logs, and published artifacts.

Before provisioning, check the available GPU memory, current hourly rate, expected runtime, and remaining approved budget. Spending across GPU and API providers counts toward the same budget. On October 25, 2026 the user raised the cumulative cap to **$20**. Switching providers does not reset or increase that cap.

Provision on demand, set a spending/runtime cutoff, collect artifacts during execution, and terminate resources after the run. Record the provider, GPU, software environment, runtime, billing, and termination evidence with each experiment.

The latest completed [HateXplain ledger](hatexplain/progress.json) records **$12.12119753456 cumulative spend**, leaving **$7.87880246544** within the $20 cap. Its GPU.ai run cost $1.34 and the instance is terminated. Earlier studies are recorded in the [Qwen ledger](qwen-policy/progress.json), [frontier API ledger](frontier-api/progress.json), and [policy-transfer ledger](policy-transfer/progress.json). Consult the latest ledger before starting new paid work. This provider preference does not reserve a GPU or start an experiment.
