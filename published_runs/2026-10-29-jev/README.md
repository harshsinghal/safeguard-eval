# Jev 1.14 on WildGuard and HateXplain

This archive records a bounded comparison using OpenRouter's Decisions API and
the resolved model `typesafe/jev-1.14-20261014` from TypeSafe. No model-weight
updates or rented GPUs. All test configurations were selected before test
inference; the official tests were already used in earlier studies.

Read the [plain-language explanation](READOUT.md), [full results](RESULTS.md),
[policy edits](POLICY-CHANGES.md), [registered plan](PLAN.md), and [notes](NOTES.md).

| Task | Brief/native | Selected policy/native | Selected policy/threshold tuned |
|---|---:|---:|---:|
| WildGuardTest, 1,699 prompts | 89.35% | 90.17% | 89.94% |
| HateXplain, 1,924 posts | 69.33% | 75.16% | 80.67% |

HateXplain's final accuracy came with only 59.93% hate-speech recall. The
threshold-tuned brief control reached 79.47%, so policy writing alone did not
produce the entire gain. See the confusion counts and comparisons before drawing
a model-selection conclusion. This does not establish architecture superiority.

## Reproduce on CPU without credentials or paid inference

From this archive directory, with Python 3.10 or later:

```sh
PYTHONPATH=source python3 -m evals.jev.report reproduce --bundle .
```

No third-party Python packages are required. This verifies the archive checksums,
native response parsing, all prediction populations, validation-selected policies
and thresholds, test metrics, paired intervals, and successful-request billing.
It writes `reproduction.json`. It does not rerun Jev or reconstruct its weights.

## Contents and provenance

- `registration.json`: pre-inference source and data hashes; unchanged plan.
- `policies/`: native question definitions and demonstration provenance.
- `policies-freeze.json`: policy identities fixed before validation.
- `freeze.json`: both tasks' policy and threshold selections fixed before tests.
- `predictions/`: fitting, validation, and test predictions without input text.
- `responses/`: original API answers, usage, request hashes, and observed latency.
- `references/` and `references.json`: aligned earlier predictions and source hashes.
- `results.json`: metrics, slices, registered comparisons, and marked descriptive
  follow-up intervals separating policy and threshold changes.
- `costs.json`: settled ledger totals, including connectivity.
- `source/`: archived evaluation/analysis code and tests.
- `checksums.json`: content hashes for the evidence package.

The fitting/validation/test sizes are 1,024/512/1,699 for WildGuard and
1,024/1,920/1,924 for HateXplain. The WildGuard target is prompt harmfulness;
HateXplain maps hate speech to BLOCK and offensive/normal to ALLOW. Neither is a
three-way REVIEW benchmark.

Gated WildGuard demonstration texts are withheld from the public archive, as in
earlier studies. Their selected training IDs, labels, text hashes, original
question hashes, and serialized lengths are retained. The redacted question is
explicitly marked and is not an inference-ready replacement for the original.
Exact requests and original datasets remain in the private local run. Re-running
inference requires access to the pinned source data and an OpenRouter credential;
the CPU result reproduction above requires neither.

The score distributions were not recalibrated. `/calibrated` in Jev result keys
means a classification cutoff selected on validation. Earlier comparison models
sometimes used learned score calibrators and different development budgets.

All **8,103 benchmark requests** succeeded and produced **22,261 classifications**.
The separate synthetic connectivity check plus benchmark usage cost
**$0.424208022**, inside a $2 ceiling. Latency summaries cover two or three policy
questions per request at up to eight concurrent requests, not a matched production
serving benchmark. No GPU cleanup is needed because none was provisioned.
