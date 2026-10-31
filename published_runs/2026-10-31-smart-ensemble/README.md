# Cross-family smart ensemble evidence

See [RESULTS.md](RESULTS.md), [PLAN.md](PLAN.md), and [AMENDMENTS.md](AMENDMENTS.md). The primary system was selected without test feedback; public tests were reused. Jev test scores were refreshed after freezing.

## Reproduce on CPU

From this directory, in an environment with `requirements.txt` installed:

```bash
PYTHONPATH=source python -m evals.smart_ensemble.study reproduce --state .
```

This refits classifiers, reselects components and validation cutoffs, and checks all scores, metrics and paired intervals. It makes no API or GPU calls. The bundle contains a checksum-verified project joblib object; only load trusted artifacts. Source prompts and private response bodies are excluded. Published Clef examples and Jev policy packs are redacted; exact private payload hashes and prior freeze provenance are in registration.json. They are not inference-ready replacements for the original data. No downloaded model weights are included.
