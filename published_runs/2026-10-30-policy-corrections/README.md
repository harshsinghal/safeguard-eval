# Training-error-derived policy corrections

[Readable findings](READOUT.md) · [Registered protocol](PLAN.md) ·
[Full tables](RESULTS.md) · [CSV](results.csv) · [Reproduction](RUNNING.md)

This bundle records one bounded policy-authoring round for Shieldstral 3B and
a prespecified transfer check on Qwen3.5-4B. Model weights remain fixed. No new
classifier head or backbone fine-tuning is performed. Exact additions, source
error IDs, ambiguity flags, unused-group audit, staged freezes, all development
outputs and selected final outputs are preserved.

The additional 2,048-example project holdout comes from previously unevaluated
WildGuardTrain groups, with model-derived labels. The 1,699-example WildGuardTest
has been inspected before and remains a separate exploratory comparison. Neither
constitutes evidence of no upstream model training exposure. Source prompts are
not redistributed. All source labels are retained, including ambiguous cases.

From this directory, install the CPU requirements, then run:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m evals.policy_corrections.study verify --state .
```

This reproduces validation selection, all final operating points, category slices
and the twelve prespecified paired bootstrap contrasts without GPU calls or source
prompt text. To repeat inference, follow RUNNING.md in a fresh working directory
and restore authorized dataset inputs. Do not overwrite this immutable record.

Billing is reconciled and compute terminated; see [billing](billing.json).
The evidence remains separate from the repository's common-validation leaderboard.
Checksums cover every file except the checksum file itself. Model/data publisher
terms continue to apply.
