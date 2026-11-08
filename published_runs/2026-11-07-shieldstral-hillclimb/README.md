# Shieldstral hill-climb evidence

[Readout](../../docs/shieldstral-hillclimb/README.md) ·
[Registered plan](../../docs/shieldstral-hillclimb/PLAN.md) ·
[Reproduction](../../docs/shieldstral-hillclimb/RUNNING.md)

The archive contains hashed case manifests, FIT mining scores, optimizer
step logs, frozen calibration and selection, paired evaluation scores,
GPU telemetry, failed attempts and the scorecard. Checkpoint and source
hashes identify local artifacts. The archive contains no source text or
model weights.

Recompute the nomination and scorecard with the study's Python
environment. This check requires no GPU or model load.

```sh
python -B tools/verify_shieldstral_hillclimb.py published_runs/2026-11-07-shieldstral-hillclimb
```
