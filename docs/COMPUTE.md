# Compute for future experiments

Use **GPU.ai first**, with **Runpod as the fallback** when GPU.ai credits are exhausted or the required GPU capacity is unavailable. The project owner has provided Runpod API credentials in a suitably named file under `~/workspace/KEYS`; read credentials locally when needed and keep their values out of source control, logs, and published artifacts.

Before provisioning, check the available GPU memory, current hourly rate, expected runtime, and remaining approved budget. Spending across providers counts toward the same budget. Switching to Runpod does not reset or increase the original cumulative cap of **less than $10**.

Provision on demand, set a spending/runtime cutoff, collect artifacts during execution, and terminate resources after the run. Record the provider, GPU, software environment, runtime, billing, and termination evidence with each experiment.

The latest completed study records **$7.91 cumulative GPU spend** in its [progress ledger](qwen-policy/progress.json). Consult that ledger and any subsequent experiment ledgers before starting new paid work. This provider preference does not reserve a GPU or start an experiment.
