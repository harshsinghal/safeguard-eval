# Jev experiment notes

## 29 October 2026 — request and interface discovery

Harsh requested Jev on the existing WildGuard and HateXplain classification tasks,
including a simple test of whether the written policy can be tuned. The teaching
article series was recorded separately in
[STUDENT-CURRICULUM.md](../research-directions/STUDENT-CURRICULUM.md) and parked.

The first discovery pass found TypeSafe's native API and no TypeSafe credential
among the locally named key files. Harsh pointed out OpenRouter availability.
OpenRouter's standard `/api/v1/models` response listed `typesafe/jev-router`, but
its official documentation exposed the separate Decisions API and actual Jev
decision models. The router is not an acceptable substitute: it chooses other
models to answer a request. A synthetic, non-benchmark request to the Decisions
endpoint succeeded with `typesafe/jev-1.14`, resolving to
`typesafe/jev-1.14-20261014` from TypeSafe. Its reported charge was $0.000014196.

Jev accepts content as state and natural-language instructions and criteria as
typed questions. This makes request-level policy adaptation possible. We do not
infer its undisclosed parameter count or internal architecture from the System
One label. Provider claims of calibrated scores or valid types are not evidence
of accuracy on our two tasks.

## Registration and data checks

The plan, native interface, three-candidate search, example-selection algorithm,
threshold grid, metrics, and $2 cap were recorded before benchmark inference.
The source code and exact data files were hashed in `registration.json`.

- WildGuard: 1,024 fitting, 512 validation, and the earlier 1,699 labeled official
  WildGuardTest prompts; target is prompt harmfulness only.
- HateXplain: 1,024 fitting, 1,920 validation, and all 1,924 official test posts;
  hate → BLOCK, offensive/normal → ALLOW.
- No ID, prompt hash, or recorded duplicate group overlaps across these splits.
- Responses are checked for exact model/provider identity and both probabilities.
  The BLOCK probability, not the separate confidence field, is the score.
- Nine tests covered native output handling, rejected identities/distributions,
  metadata exclusion, budget concurrency/persistence, training-only examples,
  validation-only selection, and failure-aware metrics.

No benchmark inference was performed with the Jev Router, a chat-completions
endpoint, an alternative decision model, or a rented GPU.

## Fitting and validation

Run brief and detailed questions together on each fitting example. Reuse the
original baseline policies through native instructions/criteria, omitting the old
demonstrations. Add four fitting examples by the registered rule: two BLOCK and
two ALLOW, preferring detailed-policy errors and unanimous labels when available.
Do not use validation or test examples. Freeze these variants before validation.

| Task | Brief validation accuracy | Detailed | Detailed + four fitting examples |
|---|---:|---:|---:|
| WildGuard | 91.21% | 91.60% | 91.99% |
| HateXplain | 70.73% | 74.06% | 76.77% |

Validation selected `examples` for both tasks at the native Choice decision.
The selected score thresholds were 0.60 for WildGuard and 0.90 for HateXplain.
The separately calibrated brief controls selected 0.55 and 0.96 respectively.
These are empirical validation choices, not universal recommended cutoffs.

Both tasks' selections, thresholds, implementation, policy hashes, validation
evidence, and dataset manifests were frozen before either official test run.
Development API charges through validation, including connectivity, totalled
$0.212884770. This is a development observation, not a test accuracy result.

## Interpretation boundaries fixed before test results

The brief-to-detailed contrast adds several kinds of guidance together. It does
not isolate the causal contribution of one word or clause. The examples contrast
adds four selected training cases; it does not establish that demonstrations
always improve a model. Threshold changes are a separate adaptation step.

We reuse previously examined public test sets and older policies. We do not know
whether Jev or any comparator encountered the benchmarks during training. Older
calibrators and ensembles used different development budgets. Compare complete
configurations and report uncertainty, without attributing differences to a
particular architecture or claiming that fine-tuning is generally unnecessary.

## Completed test inference and analysis

All 8,103 benchmark requests succeeded, returning 22,261 typed classifications
from the expected model/provider. There were no retries, failed classifications,
or unreconciled reservations. Connectivity plus benchmark charges totalled
$0.424208022. No GPUs were rented. The previous experiment subtotal plus this
extension is $12.92540555656; skill-agent conversation costs remain separately
documented and are not represented by this subtotal.

| Task | Brief/native | Detailed/native | Examples/native | Selected/threshold tuned |
|---|---:|---:|---:|---:|
| WildGuard | 89.35% | 90.05% | 90.17% | 89.94% |
| HateXplain | 69.33% | 72.77% | 75.16% | 80.67% |

Native policy gains: +0.82 points on WildGuard, +5.82 on HateXplain. The WildGuard
cutoff adjustment lost four correct test decisions; it remains in the results.
The HateXplain cutoff adjustment reduced false blocks by 256 but added 150 missed
hate posts compared with the selected policy's native choice. Hate-class recall
fell from 85.19% to 59.93%, and hate-class F1 fell even as accuracy and macro-F1 rose.

The threshold-tuned brief HateXplain control scored 79.47%, showing that much of
the apparent gain over 69.33% comes from the operating cutoff. The selected
policy with its cutoff scored 1.20 points above the brief policy with its own
cutoff. Do not attribute the full 11.33-point gain to policy wording alone.

After inspecting the first result tables, we added three descriptive paired
intervals to separate (1) policy wording at native Choice, (2) threshold changes
on the selected policy, and (3) selected versus brief with both thresholds tuned.
This is a post-run analysis addition, not a new registered primary comparison.
No policies, selection criteria, thresholds, dataset rows, or inference changed.

“Calibrated” in the machine-readable Jev arm names denotes only a selected
threshold. Probabilities are not rescaled and no score-calibration model is fit.
Historical individual references did use trained calibrators; those comparisons
are clearly labeled. Benchmark calibration metrics use probabilities clipped to
[1e-7, 1-1e-7] for numerical stability. Single-label category slices should be read
as recall or false-block rates; their fixed-two-class macro-F1 is not meaningful
as a cross-category ranking.

Public evidence includes native API responses, prompt-free predictions, exact
split hashes, policies, selection records, paired comparisons, and costs. Gated
WildGuard training demonstrations remain private. Their IDs/hashes and original
question sizes are preserved for provenance and selection reproduction, and the
public example-bearing question is explicitly marked as redacted.

The CPU reproduction passed using the archived source from the evidence directory:
metrics, validation choices, paired intervals, and successful-request billing
matched exactly. No API calls were made for reproduction. Eleven focused tests
passed, and the public additions passed credential-pattern and gated-text scans.
