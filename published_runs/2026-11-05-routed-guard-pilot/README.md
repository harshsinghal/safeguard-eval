# Routed guard system pilot evidence

This archive records the locally registered plan, calibration and evaluation
metadata, frozen model mapping, fresh single-model controls and actual routed
HTTP decisions, whole-system scores, preflight outcomes and cleanup.
An unchanged supplementary repeat preserves durable device telemetry and confirms
the primary decisions. Primary full-run worker telemetry was not retained; the
repeat is explicitly separate and does not replace the primary result.

[Readout](../../docs/routed-guard/README.md) ·
[Serving API](../../docs/routed-guard/RUNNING.md)

JSON Lines and large JSON files use deterministic gzip. SHA256SUMS binds every
artifact. Reproduce selection, system metrics and guard traces without source
prompts, weights, GPU or API credentials:

```bash
python -B tools/verify_routed_guard_evidence.py --archive published_runs/2026-11-05-routed-guard-pilot
```

The parent fixed suite supplies the original policies/profiles. This is a
112-case pilot with reused tests and mixed reference provenance, not the full
983-case score or a combined-policy enterprise audit. Source text, weights,
private configuration, process receipts and worker logs are excluded.
