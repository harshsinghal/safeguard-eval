# Complete policy-search ledger

Accuracy on 1,024 fitting / 512 validation rows (%). These are selection results, not official-test results. Each model evaluates shared p0/p1/p2 and its own p3/p4. The winner is chosen by validation accuracy, then the registered tie-break.

| Model | p0 | p1 | p2 | specific p3 | specific p4 | Selected |
|---|---:|---:|---:|---:|---:|---|
| policylm | 88.38 / 90.23 | 84.38 / 86.91 | 91.99 / 90.04 | 87.60 / 89.65 | 91.70 / 91.80 | wg-p4-policylm-compact |
| shieldstral | 95.61 / 95.51 | 96.48 / 96.48 | 98.44 / 98.44 | 98.24 / 98.44 | 98.54 / 98.63 | wg-p4-shieldstral-taxonomy-priority |
| cope | 93.26 / 94.34 | 93.65 / 93.16 | 93.85 / 93.95 | 94.63 / 95.31 | 94.14 / 94.14 | wg-p3-cope-social-and-deception |
| safeguard | 91.11 / 91.99 | 91.70 / 92.58 | 91.41 / 92.58 | 91.50 / 92.38 | 91.89 / 91.80 | wg-p2-boundary-checklist |

The shared winner is `wg-p2-boundary-checklist`. The preselected primary is `shieldstral / wg-p4-shieldstral-taxonomy-priority`.

All policy texts and fitting-derived rationales are in [the registry](../../evals/wildguard/registry.json); exact scores, confusion matrices, failures and hashes are in [selection.json](selection.json). Validation prompts were not inspected to draft policies, but aggregate validation scores were visible during the search.

WildGuard is a fixed baseline, not a policy candidate: fitting accuracy 99.707% (one parsing error), validation accuracy 100%. Those internal partitions come from its original weight-training dataset.
