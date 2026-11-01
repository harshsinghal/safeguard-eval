# Retrieved-example accuracy study

Frozen policy-only, fixed-four, nearest-four and balanced-nearest comparisons for PolicyLM, Shieldstral, Kev and Jev, plus a shared nearest-neighbor vote. No calibration.

See [results](RESULTS.md), [protocol](PLAN.md), [research notes](NOTES.md), [costs](billing.json), and [cleanup](cleanup.json). Source prompts and embeddings are excluded.

PLAN.md preserves the initial registration. Subsequent budget authorization and technical amendments are recorded in NOTES.md and the registration history.

Reproduce on CPU from a checkout of the repository:

```bash
python3 tools/verify_retrieved_examples.py --archive published_runs/2026-11-01-retrieved-examples
```

The verifier checks all hashes, restores compressed predictions in a temporary folder, and recomputes validation nominations, final metrics and paired bootstrap differences.
