# HateXplain: structured policy, omissions, and wording transfer

Completed 26 October 2026. Read the [plain-language findings](../../docs/hatexplain/READOUT.md)
first. This bundle retains all 45 classifier runs and all seven policy files,
including drafts excluded before validation. It contains 73,452 classifications
and zero classifier output failures. Six unsuccessful editor calls and six amended
calls are indexed separately in [authoring-index.json](source/docs/hatexplain/authoring-index.json).
Raw post text and raw editor traces remain private, except for the four licensed
training demonstrations included in policy text.

The intended rule is BLOCK hate speech, ALLOW offensive-but-not-hateful and normal
posts. These are binary decisions under one rule, not complete platform judgments
or REVIEW routing. Classifier weights, native interfaces, and decision settings
were fixed. Specialist cutoffs stayed at 0.5, without calibration. Scores describe
these configurations, not each model's best achievable performance.

## What was frozen

- [Plan](source/docs/hatexplain/PLAN.md), [model registry](source/evals/hatexplain/registry.json),
  [data manifest](source/docs/hatexplain/data-manifest.json), and [example provenance](source/docs/hatexplain/example-provenance.json).
- [Original registration](registration.json) and [source guard amendment before inference](source-amendment-before-inference.json).
- [Editor contract amendment](source/docs/hatexplain/AUTHORING-AMENDMENT.md),
  [amendment identity](authoring-amendment.json), [scope review](source/docs/hatexplain/SCOPE-REVIEW.md),
  and [eligibility gate](eligibility.json). Scope review was AI-assisted, not independent human adjudication.
- [Final freeze](freeze.json) and [test upload record](test-upload.json). Freeze SHA-256:
  `9e2181c8ffdadf03e2c975865b7e60c0968dda18c4d1e4e8711560f67d4b7731`.
- [Exact policies](policies), [wording changes](source/docs/hatexplain/POLICY-CHANGES.md),
  per-run rendered policies and prediction records in [runs](runs), and pinned [runtime environments](runtime).

There are nine fitting runs on 1,024 posts, six eligible validation runs on 1,920
posts, 27 full-test conditions on all 1,924 official test posts, and three repeats
on 256 test posts. Full-test class counts: 594 hate, 548 offensive, 782 normal.
Original three-class majority voting preceded binary mapping. Cross-split duplicate
groups were quarantined from earlier splits; the test was preserved. The source
policy is our operational formulation, not an official verbatim annotation guideline.

## Validation selection and held-out results

Selection used binary macro-F1, then accuracy, shorter text and policy ID. Format
and omission arms were prespecified diagnostics, not selected on the test. PolicyLM
retained the unchanged shared policy; it did not produce an eligible new revision.

| Recipient | Selected text | Validation macro-F1 (%) | Test macro-F1 (%) | Test accuracy (%) |
|---|---|---:|---:|---:|
| PolicyLM 1.7B | `p0` | 65.897 | 63.874 | 68.711 |
| Shieldstral 3B | `shieldstral-p2` | 53.795 | 52.946 | 53.170 |
| Qwen3.5-4B | `qwen-4b-p1` | 74.412 | 71.270 | 72.505 |

Macro-F1 is the mean of the two class F1 scores; it weights ALLOW and BLOCK equally.
ERROR would be scored as wrong, including a conservative opposite-gold-class
assignment in F1. No classifier errors occurred. “Selected” refers to this limited
candidate pool and validation objective, not a global optimum.

## Complete test matrix

All percentages below use the same 1,924 posts. Missed hate is out of 594; false
blocks of offensive and normal posts are out of 548 and 782 respectively. PolicyLM
rows called `markdown` use the native category-field renderer: they are not a
whole-document Markdown treatment. `p0` is the shared reference; other IDs are the
frozen source-selected revisions. Omissions apply to p0 only.

| Model | Policy | Variant | Accuracy (%) | Macro-F1 (%) | Missed hate | Offensive false blocks | Normal false blocks |
|---|---|---|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | `p0` | `markdown` | 68.71 | 63.87 | 285 | 194 | 123 |
| PolicyLM 1.7B | `p0` | `omit-definitions` | 70.17 | 63.85 | 321 | 167 | 86 |
| PolicyLM 1.7B | `p0` | `omit-exceptions` | 70.32 | 65.19 | 287 | 170 | 114 |
| PolicyLM 1.7B | `p0` | `omit-allow-examples` | 67.72 | 63.13 | 282 | 208 | 131 |
| PolicyLM 1.7B | `p0` | `omit-all-examples` | 66.63 | 62.57 | 270 | 222 | 150 |
| PolicyLM 1.7B | `qwen-4b-p1` | `markdown` | 67.36 | 62.98 | 277 | 209 | 142 |
| PolicyLM 1.7B | `shieldstral-p2` | `markdown` | 70.27 | 64.60 | 303 | 167 | 102 |
| Shieldstral 3B | `p0` | `markdown` | 52.39 | 52.11 | 16 | 472 | 428 |
| Shieldstral 3B | `p0` | `omit-definitions` | 50.73 | 50.27 | 14 | 482 | 452 |
| Shieldstral 3B | `p0` | `omit-exceptions` | 52.34 | 52.05 | 16 | 470 | 431 |
| Shieldstral 3B | `p0` | `omit-allow-examples` | 50.26 | 49.74 | 13 | 483 | 461 |
| Shieldstral 3B | `p0` | `omit-all-examples` | 60.97 | 60.92 | 40 | 410 | 301 |
| Shieldstral 3B | `p0` | `linear` | 57.28 | 57.26 | 27 | 440 | 355 |
| Shieldstral 3B | `p0` | `tagged` | 52.81 | 52.57 | 18 | 468 | 422 |
| Shieldstral 3B | `p0` | `reordered` | 54.21 | 54.05 | 16 | 466 | 399 |
| Shieldstral 3B | `qwen-4b-p1` | `markdown` | 51.92 | 51.59 | 15 | 476 | 434 |
| Shieldstral 3B | `shieldstral-p2` | `markdown` | 53.17 | 52.95 | 16 | 469 | 416 |
| Qwen3.5-4B | `p0` | `markdown` | 72.45 | 71.25 | 94 | 254 | 182 |
| Qwen3.5-4B | `p0` | `omit-definitions` | 71.31 | 70.24 | 90 | 268 | 194 |
| Qwen3.5-4B | `p0` | `omit-exceptions` | 73.02 | 71.77 | 94 | 247 | 178 |
| Qwen3.5-4B | `p0` | `omit-allow-examples` | 70.37 | 69.40 | 89 | 272 | 209 |
| Qwen3.5-4B | `p0` | `omit-all-examples` | 61.80 | 61.70 | 48 | 373 | 314 |
| Qwen3.5-4B | `p0` | `linear` | 70.63 | 69.73 | 81 | 284 | 200 |
| Qwen3.5-4B | `p0` | `tagged` | 73.91 | 72.25 | 118 | 227 | 157 |
| Qwen3.5-4B | `p0` | `reordered` | 69.65 | 68.84 | 79 | 292 | 213 |
| Qwen3.5-4B | `qwen-4b-p1` | `markdown` | 72.51 | 71.27 | 96 | 255 | 178 |
| Qwen3.5-4B | `shieldstral-p2` | `markdown` | 72.71 | 71.46 | 96 | 252 | 177 |

[CSV table](conditions.csv) and [complete analysis](analysis.json) retain full precision,
confusion matrices, agreement and platform slices, and overlapping target slices
with at least 30 posts. Target slices are descriptive, not causal fairness tests.

## Paired comparisons

Changes are in percentage points. Each pair uses the same posts and a paired
bootstrap of duplicate groups (2,000 resamples, seed 20261026). Intervals are 95%,
unadjusted for multiple comparisons, and exclude policy-search and inference
variation. They should not be treated as confirmatory tests selected after viewing
these results. “Fixed / broken” counts errors corrected / correct decisions lost.

| Recipient | Policy / variant | Reference | Accuracy change [95% interval] | Macro-F1 change [95% interval] | Fixed / broken |
|---|---|---|---:|---:|---:|
| PolicyLM 1.7B | `p0` / `omit-definitions` | `p0` | +1.46 [+0.26, +2.65] | -0.02 [-1.39, +1.26] | 81 / 53 |
| PolicyLM 1.7B | `p0` / `omit-exceptions` | `p0` | +1.61 [+0.42, +2.81] | +1.31 [+0.01, +2.63] | 83 / 52 |
| PolicyLM 1.7B | `p0` / `omit-allow-examples` | `p0` | -0.99 [-1.82, -0.10] | -0.74 [-1.61, +0.17] | 25 / 44 |
| PolicyLM 1.7B | `p0` / `omit-all-examples` | `p0` | -2.08 [-3.22, -0.88] | -1.31 [-2.48, -0.04] | 45 / 85 |
| PolicyLM 1.7B | `qwen-4b-p1` / `markdown` | `p0` | -1.35 [-2.18, -0.57] | -0.90 [-1.76, -0.06] | 18 / 44 |
| PolicyLM 1.7B | `shieldstral-p2` / `markdown` | `p0` | +1.56 [+0.62, +2.54] | +0.73 [-0.32, +1.78] | 59 / 29 |
| Shieldstral 3B | `p0` / `omit-definitions` | `p0` | -1.66 [-2.29, -1.09] | -1.83 [-2.53, -1.19] | 3 / 35 |
| Shieldstral 3B | `p0` / `omit-exceptions` | `p0` | -0.05 [-0.47, +0.36] | -0.06 [-0.51, +0.39] | 8 / 9 |
| Shieldstral 3B | `p0` / `omit-allow-examples` | `p0` | -2.13 [-2.91, -1.40] | -2.36 [-3.24, -1.56] | 8 / 49 |
| Shieldstral 3B | `p0` / `omit-all-examples` | `p0` | +8.58 [+7.17, +9.99] | +8.81 [+7.40, +10.26] | 190 / 25 |
| Shieldstral 3B | `p0` / `linear` | `p0` | +4.89 [+3.79, +6.03] | +5.16 [+4.08, +6.29] | 107 / 13 |
| Shieldstral 3B | `p0` / `tagged` | `p0` | +0.42 [-0.36, +1.25] | +0.46 [-0.40, +1.36] | 35 / 27 |
| Shieldstral 3B | `p0` / `reordered` | `p0` | +1.82 [+1.20, +2.45] | +1.94 [+1.30, +2.63] | 37 / 2 |
| Shieldstral 3B | `qwen-4b-p1` / `markdown` | `p0` | -0.47 [-0.88, -0.10] | -0.51 [-0.96, -0.11] | 3 / 12 |
| Shieldstral 3B | `qwen-4b-p1` / `markdown` | `shieldstral-p2` | -1.25 [-1.77, -0.73] | -1.35 [-1.94, -0.80] | 3 / 27 |
| Shieldstral 3B | `shieldstral-p2` / `markdown` | `p0` | +0.78 [+0.36, +1.20] | +0.84 [+0.40, +1.30] | 16 / 1 |
| Qwen3.5-4B | `p0` / `omit-definitions` | `p0` | -1.14 [-1.98, -0.31] | -1.00 [-1.80, -0.17] | 22 / 44 |
| Qwen3.5-4B | `p0` / `omit-exceptions` | `p0` | +0.57 [-0.05, +1.20] | +0.53 [-0.08, +1.17] | 24 / 13 |
| Qwen3.5-4B | `p0` / `omit-allow-examples` | `p0` | -2.08 [-3.01, -1.19] | -1.85 [-2.75, -0.98] | 19 / 59 |
| Qwen3.5-4B | `p0` / `omit-all-examples` | `p0` | -10.65 [-12.32, -8.89] | -9.55 [-11.20, -7.89] | 50 / 255 |
| Qwen3.5-4B | `p0` / `linear` | `p0` | -1.82 [-2.65, -0.99] | -1.52 [-2.35, -0.72] | 19 / 54 |
| Qwen3.5-4B | `p0` / `tagged` | `p0` | +1.46 [+0.42, +2.45] | +1.01 [-0.04, +1.98] | 62 / 34 |
| Qwen3.5-4B | `p0` / `reordered` | `p0` | -2.81 [-3.73, -1.87] | -2.41 [-3.29, -1.52] | 15 / 69 |
| Qwen3.5-4B | `qwen-4b-p1` / `markdown` | `p0` | +0.05 [-0.31, +0.47] | +0.02 [-0.35, +0.41] | 8 / 7 |
| Qwen3.5-4B | `shieldstral-p2` / `markdown` | `p0` | +0.26 [-0.26, +0.83] | +0.21 [-0.27, +0.74] | 16 / 11 |
| Qwen3.5-4B | `shieldstral-p2` / `markdown` | `qwen-4b-p1` | +0.21 [-0.26, +0.68] | +0.19 [-0.26, +0.64] | 12 / 8 |

## Repeatability and interpretation limits

Reference decisions changed on 0/256 PolicyLM posts, 1/256 Shieldstral posts, and
1/256 Qwen posts when repeated. The repeat uses a subset, so its accuracy should
not be compared directly with the complete test. Exact baseline-subset and repeat
scores are in analysis.json.

The editor had only two repaired rounds per recipient, produced little diversity,
and used AI-assisted scope review. Its failed initial calls remain documented.
Qwen's selected text differs only in punctuation; Shieldstral's adds a context
clarification to those edits. The transfer pool therefore has only two new texts.
The large omission/presentation effects and small wording-search effects answer
different questions. Removing a section also changes information and length;
related concepts may remain elsewhere. A higher score does not certify that an
incomplete policy preserves the intended governance boundary. Public-benchmark
training exposure is unknown, and this English social-media task cannot validate
enterprise policy enforcement generally.

## Reproduce without a GPU or private data

Use Python 3.11 or later and NumPy 2.4.6. From the repository root, for example:

```sh
python3.11 -m venv /tmp/hatexplain-reproduction
/tmp/hatexplain-reproduction/bin/python -m pip install -r published_runs/2026-10-26-hatexplain/requirements-reproduce.txt
/tmp/hatexplain-reproduction/bin/python published_runs/2026-10-26-hatexplain/reproduce.py --bundle published_runs/2026-10-26-hatexplain
```

The script verifies [evidence hashes](evidence-manifest.json), decompresses complete
prediction records into a temporary directory, imports the archived implementation,
recomputes validation choices, all scores and intervals, and compares its output
exactly with analysis.json. It does not contact a model API, download a dataset,
or perform new inference. New inference is a separate reproducibility claim and
can vary with hardware and runtime.

[Private verification record](private-verification.json) reports reconstruction
of all 73,452 submitted requests and replay of all decisions from raw local traces.
Raw traces are not required for the public CPU calculation, which verifies the
recorded predictions rather than independently attesting how the model generated them.

## Compute and provenance

GPU.ai billed **$1.34** for 2,416 GPU seconds on an RTX PRO 6000 96 GB at $1.99/hour.
The instance is terminated; temporary SSH keys were removed. RunPod was not used.
[Billing](billing.json) reconciles cumulative project spend to **$12.12119753456**
of the $20 cap, leaving **$7.87880246544**.

Dataset: [HateXplain](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain),
[upstream source](https://github.com/hate-alert/HateXplain), and
[Mathew et al., AAAI 2021](https://arxiv.org/abs/2012.10289).
See [dataset license](DATASET-LICENSE.txt) and [notice](NOTICE).
Model identities: [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b),
[Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
and [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B).
