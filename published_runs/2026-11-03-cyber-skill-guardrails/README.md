# Cyber requests and complete skill packages: experiment evidence

This bundle records two separate tests: source-derived CyberSecEval request
classification and static screening of eligible MalSkillBench textual packages.
The scores do not measure attack success, safe execution, or all packages in the
upstream collections.

Start with the [plain-language readout](../../docs/cyber-skill-guardrails/README.md),
[result tables](../../docs/cyber-skill-guardrails/RESULTS.md) and
[methods](../../docs/cyber-skill-guardrails/METHODS.md).

## What is preserved

| Record | Purpose |
|---|---|
| [registration.json](registration.json) | Source, input, policy and implementation hashes; model revisions and selection rules |
| [freeze.json](freeze.json) and [freeze-publication.json](freeze-publication.json) | Validation-selected configurations and confirmation that their GitHub publication preceded test inference |
| [validation-summary.json](validation-summary.json) | All registered candidate validation results |
| [results.json](results.json) | Final metrics, error counts, uncertainty, paired comparisons, seed sensitivity and descriptive slices |
| [predictions](predictions) | Per-example scores and decisions, without raw input text |
| [policies](policies) | Exact policy candidates rendered for each model |
| [metadata](metadata), [data audit](data-audit.json), [source manifest](source-manifest.json), [package manifest](package-manifest.jsonl) | Population, exclusions, grouping, labels and restoration hashes |
| [learned](learned) | Head-selection grids and hashes of privately retained features and fitted checkpoints |
| [runtime](runtime) | Dependency versions, runtime recipes, feature summaries and adapter checks |
| [amendments](amendments) | Pre-test corrections, including the cyber source-format confound and native Llama Guard readout |
| [billing.json](billing.json), [API ledger summary](jev-billing.json), [cleanup.json](cleanup.json) | Reconciled cost and resource termination |
| [source](source) and [artifact-manifest.json](artifact-manifest.json) | Archived implementation and checksums for this public bundle |

Neural results use the first registered seed as primary and report all three.
The separately trained Jina document-only heads are not the same-classifier input
ablation used for prompted models. Prompt Guard is a narrower diagnostic control.
All original split assignments were retained through the cyber pre-test repair.

## Reproduce the published measurements

Use Python 3.12, numpy 2.5.4, scipy 1.18.1 and scikit-learn 1.9.1. From the
repository root:

```sh
python scripts/reproduce_cyber_skill_guardrails.py \
  --run published_runs/2026-11-03-cyber-skill-guardrails
python scripts/verify_cyber_skill_guardrails_metrics.py \
  --run published_runs/2026-11-03-cyber-skill-guardrails
```

The first command verifies the public-file manifest, imports the archived report
implementation and recomputes all final metrics and intervals in a temporary
directory. It requires an exact JSON match. The second independently checks
confusion counts and scikit-learn metrics for final policies, input views,
controls and neural seeds. Neither command downloads models or makes paid calls.

For inference-input restoration and new experiments, see the
[run instructions](../../docs/cyber-skill-guardrails/RUNNING.md). Raw benchmark
text, embedding vectors, fitted joblib files, model weights, private API responses
and infrastructure credentials are not in this bundle. Their safe provenance or
hashes are retained where relevant. Obtain upstream inputs under their licenses;
MalSkillBench restricts use to academic research.

An inference rerun needs its own outputs, authorization, ledger and selection
freeze. Different runtimes may not reproduce floating-point features or model
scores bit for bit. Do not overwrite this archive or treat the existing test
results as new validation data while calling a later choice preregistered.

The preserved pilot and failed adapter readouts are diagnostic history. They are
excluded from the primary results. Engineering repairs were completed before
test inference, and their costs remain included in the bill.
