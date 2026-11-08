# Shieldstral fine-tuning evidence

[Results and limitations](../../docs/shieldstral-policy/README.md) ·
[Registered plan](../../docs/shieldstral-policy/PLAN.md) ·
[Local reproduction](../../docs/shieldstral-policy/RUNNING.md)

This archive contains the input and model hashes, paired yes/no scores,
validation cutoffs, training step records, timing and sampled GPU telemetry.
It retains the frozen base and both adapter runs. The timeline records local
filesystem modification times for the original stage outputs. The bundle
keeps restricted source text and adapter weights in local ignored storage.

With Python and NumPy, verify the complete scorecard without prompts,
model weights, credentials or a GPU.

```sh
python -B tools/verify_shieldstral_policy.py published_runs/2026-11-07-shieldstral-policy
```
