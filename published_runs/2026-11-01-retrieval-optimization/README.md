# Staged retrieval optimization evidence

Model-specific formatting, stronger embeddings, example selection, and library coverage with fixed classifier weights and decision rules. See [results](RESULTS.md), [plan](PLAN.md), [notes](NOTES.md), [costs](billing.json), and [cleanup](cleanup.json).

Source prompts, vectors, request bodies, API response bodies and credentials are excluded. Example IDs, scores, request hashes and prediction provenance are retained.

Reproduce with NumPy on CPU, without model downloads or credentials:

```bash
python3 tools/verify_retrieval_optimization.py --archive published_runs/2026-11-01-retrieval-optimization
```
