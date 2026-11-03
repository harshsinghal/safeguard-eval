# Code embeddings and Qwen: results

All choices were frozen on validation before new test inference. Neural primary
results use seed 20261103; the other two seeds are shown below. The Jina backbones
stay frozen. These are static artifact classifications, not execution tests.

[Methods and limits](METHODS.md) · [Pre-test freeze](preparation/README.md) · [Machine-readable results](../../published_runs/2026-11-03-artifact-representations/results.json) · [Prior eight-system results](../malicious-artifacts/RESULTS.md)

## Source files: 160 test records

| System | Accuracy | Balanced accuracy (95% CI) | Macro F1 | MCC | False blocks | Missed threats |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5 9B · six-policy search | 88.75% | 88.75% (83.56%–93.37%) | 88.61% | 0.795 | 0/80 | 18/80 |
| Jina v2 code + logistic | 88.75% | 88.75% (83.70%–93.89%) | 88.74% | 0.776 | 7/80 | 11/80 |
| Jina v2 code + neural head | 88.75% | 88.75% (83.33%–94.34%) | 88.73% | 0.777 | 6/80 | 12/80 |
| Qwen3.5 4B · six-policy search | 86.88% | 86.88% (81.58%–92.37%) | 86.64% | 0.764 | 0/80 | 21/80 |
| Jina code 0.5B + logistic | 84.38% | 84.38% (77.73%–91.63%) | 84.24% | 0.700 | 5/80 | 20/80 |
| Jina code 0.5B + neural head | 84.38% | 84.38% (77.16%–91.66%) | 84.20% | 0.704 | 4/80 | 21/80 |

All final outputs resolved. Rows are observed test scores of frozen choices; this
ordering does not select a new configuration or a universal deployment winner.

## Agent-skill text: 1,384 test records

| System | Accuracy | Balanced accuracy (95% CI) | Macro F1 | MCC | False blocks | Missed threats |
|---|---:|---:|---:|---:|---:|---:|
| Jina code 0.5B + logistic | 59.18% | 57.26% (52.76%–61.72%) | 57.26% | 0.145 | 282/545 | 283/839 |
| Qwen3.5 9B · six-policy search | 46.10% | 55.48% (52.92%–58.82%) | 39.79% | 0.210 | 2/545 | 744/839 |
| Jina v2 code + logistic | 57.73% | 54.88% (48.15%–60.48%) | 54.90% | 0.100 | 319/545 | 266/839 |
| Qwen3.5 4B · six-policy search | 45.30% | 54.85% (52.58%–57.90%) | 38.48% | 0.199 | 1/545 | 756/839 |
| Jina code 0.5B + neural head | 57.37% | 54.58% (50.00%–58.62%) | 54.60% | 0.093 | 319/545 | 271/839 |
| Jina v2 code + neural head | 50.29% | 48.49% (40.14%–55.91%) | 48.47% | -0.030 | 327/545 | 361/839 |

All final outputs resolved. Rows are observed test scores of frozen choices; this
ordering does not select a new configuration or a universal deployment winner.

## Policy search: development and test

| Task | Qwen | Selected policy | Selected validation BA | Brief test BA | Selected test BA | Test change, pp (paired 95% CI) |
|---|---|---|---:|---:|---:|---:|
| code | qwen4 | brief | 94.58% | 86.88% | 86.88% | +0.00 (+0.00 to +0.00) |
| code | qwen9 | behavior | 94.17% | 86.25% | 88.75% | +2.50 (+0.58 to +5.06) |
| skills | qwen4 | scope | 67.58% | 54.17% | 54.85% | +0.68 (-0.16 to +1.36) |
| skills | qwen9 | contrasts | 67.58% | 55.30% | 55.48% | +0.17 (-0.55 to +0.90) |

All six validation candidates are preserved in [the validation summary](preparation/validation-summary.json).
These are comparisons of complete authored candidates. They do not isolate the
causal contribution of a single example, word or clause. No extra policy was
chosen after test evaluation.

## Neural initialization sensitivity

One configuration per embedding/task was selected by mean validation performance
across all three seeds. Each row below is a separate single head, not a seed ensemble.

| Task | Representation | Selected configuration | Seed | Test accuracy | Test BA | False blocks | Misses |
|---|---|---|---:|---:|---:|---:|---:|
| code | jina-v2-mlp | h128-a0.01-e30 | 20261103 | 88.75% | 88.75% | 6 | 12 |
| code | jina-v2-mlp | h128-a0.01-e30 | 20261104 | 90.62% | 90.62% | 6 | 9 |
| code | jina-v2-mlp | h128-a0.01-e30 | 20261105 | 90.62% | 90.62% | 6 | 9 |
| code | jina-code-mlp | h128-a0.01-e30 | 20261103 | 84.38% | 84.38% | 4 | 21 |
| code | jina-code-mlp | h128-a0.01-e30 | 20261104 | 85.00% | 85.00% | 5 | 19 |
| code | jina-code-mlp | h128-a0.01-e30 | 20261105 | 83.75% | 83.75% | 4 | 22 |
| skills | jina-v2-mlp | h128-a0.01-e60 | 20261103 | 50.29% | 48.49% | 327 | 361 |
| skills | jina-v2-mlp | h128-a0.01-e60 | 20261104 | 49.35% | 47.29% | 340 | 361 |
| skills | jina-v2-mlp | h128-a0.01-e60 | 20261105 | 47.76% | 46.11% | 336 | 387 |
| skills | jina-code-mlp | h256-a0.01-e30 | 20261103 | 57.37% | 54.58% | 319 | 271 |
| skills | jina-code-mlp | h256-a0.01-e30 | 20261104 | 57.01% | 54.22% | 321 | 274 |
| skills | jina-code-mlp | h256-a0.01-e30 | 20261105 | 56.43% | 54.03% | 312 | 291 |

## Paired comparisons with previous frozen systems

Changes are balanced-accuracy percentage points with grouped, unadjusted 95%
intervals. Negative values mean the new system scored lower. These comparisons
reuse the same benchmark and do not account for all historical search.

| Task | New system | Versus previous Qwen 4B | Versus fine-tuned Liquid | Versus TF-IDF |
|---|---|---:|---:|---:|
| code | Qwen3.5 4B · six-policy search | +0.00 (+0.00 to +0.00) | -4.38 (-10.42 to +2.34) | -1.25 (-6.17 to +3.38) |
| code | Qwen3.5 9B · six-policy search | +1.87 (-1.71 to +5.56) | -2.50 (-8.80 to +3.68) | +0.62 (-4.92 to +5.11) |
| code | Jina v2 code + logistic | +1.87 (-3.61 to +7.54) | -2.50 (-9.49 to +4.48) | +0.62 (-5.36 to +6.58) |
| code | Jina v2 code + neural head | +1.87 (-3.98 to +8.01) | -2.50 (-10.09 to +4.92) | +0.62 (-4.85 to +6.71) |
| code | Jina code 0.5B + logistic | -2.50 (-7.23 to +3.09) | -6.88 (-14.03 to +1.33) | -3.75 (-9.69 to +2.18) |
| code | Jina code 0.5B + neural head | -2.50 (-8.06 to +3.20) | -6.88 (-14.38 to +0.98) | -3.75 (-10.39 to +2.53) |
| skills | Qwen3.5 4B · six-policy search | +0.68 (+0.23 to +1.14) | -10.20 (-15.00 to -4.38) | -15.34 (-19.50 to -9.83) |
| skills | Qwen3.5 9B · six-policy search | +1.31 (+0.51 to +2.44) | -9.58 (-14.72 to -3.49) | -14.71 (-19.26 to -9.00) |
| skills | Jina v2 code + logistic | +0.71 (-7.89 to +7.63) | -10.17 (-15.35 to -5.86) | -15.31 (-20.91 to -10.63) |
| skills | Jina v2 code + neural head | -5.69 (-15.25 to +2.85) | -16.57 (-23.56 to -10.79) | -21.71 (-28.96 to -15.38) |
| skills | Jina code 0.5B + logistic | +3.09 (-1.67 to +7.47) | -7.79 (-12.89 to -1.56) | -12.93 (-17.97 to -6.60) |
| skills | Jina code 0.5B + neural head | +0.41 (-5.41 to +5.13) | -10.47 (-14.62 to -5.52) | -15.61 (-19.88 to -10.81) |

## Complete versus clipped input views

These are different item subsets, not a causal test of truncation. Source files
have 38 clipped test items; skills have 398. Both classes are retained where
present; the JSON also contains source-level slices.

| Task | System | Clipped | N | Accuracy | BA | False blocks | Misses |
|---|---|---|---:|---:|---:|---:|---:|
| code | qwen4 | False | 122 | 86.89% | 87.30% | 0 | 16 |
| code | qwen4 | True | 38 | 86.84% | 85.29% | 0 | 5 |
| code | qwen9 | False | 122 | 89.34% | 89.68% | 0 | 13 |
| code | qwen9 | True | 38 | 86.84% | 85.29% | 0 | 5 |
| code | jina-v2-lr | False | 122 | 86.89% | 86.98% | 6 | 10 |
| code | jina-v2-lr | True | 38 | 94.74% | 94.68% | 1 | 1 |
| code | jina-v2-mlp | False | 122 | 86.89% | 87.03% | 5 | 11 |
| code | jina-v2-mlp | True | 38 | 94.74% | 94.68% | 1 | 1 |
| code | jina-code-lr | False | 122 | 83.61% | 83.91% | 4 | 16 |
| code | jina-code-lr | True | 38 | 86.84% | 85.85% | 1 | 4 |
| code | jina-code-mlp | False | 122 | 83.61% | 83.97% | 3 | 17 |
| code | jina-code-mlp | True | 38 | 86.84% | 85.85% | 1 | 4 |
| skills | qwen4 | False | 986 | 47.16% | 56.54% | 1 | 520 |
| skills | qwen4 | True | 398 | 40.70% | 50.63% | 0 | 236 |
| skills | qwen9 | False | 986 | 48.38% | 57.49% | 2 | 507 |
| skills | qwen9 | True | 398 | 40.45% | 50.42% | 0 | 237 |
| skills | jina-v2-lr | False | 986 | 53.65% | 51.71% | 221 | 236 |
| skills | jina-v2-lr | True | 398 | 67.84% | 62.91% | 98 | 30 |
| skills | jina-v2-mlp | False | 986 | 46.96% | 45.88% | 228 | 295 |
| skills | jina-v2-mlp | True | 398 | 58.54% | 55.06% | 99 | 66 |
| skills | jina-code-lr | False | 986 | 59.63% | 57.96% | 192 | 206 |
| skills | jina-code-lr | True | 398 | 58.04% | 55.59% | 90 | 77 |
| skills | jina-code-mlp | False | 986 | 55.88% | 53.77% | 216 | 219 |
| skills | jina-code-mlp | True | 398 | 61.06% | 56.73% | 103 | 52 |

## Interpretation limits

Code labels are largely model-assisted and the 160-file test is small. Skill
sources are held out, but five structural families overlap fitting/test and
cover 205 test items. Missing companion files and clipped content can hide
decisive evidence. Neither checkpoint identity nor benchmark agreement proves
that a skill is safe to install. The labels do not separately validate detectors
for networking, deletion, deception or each attack type.

Frozen Jina heads use supervised fitting labels and a larger numerical search;
Qwen selects policy wording without updating weights. Older reference systems
had different search budgets. Architecture, model size and training data all
differ, so no architecture-only or cost/latency superiority follows.

Grouped bootstrap intervals use 2,000 draws, seed 20261103, package/similarity
groups for code and structural-family/benign-identity groups for skills. They
exclude label uncertainty, unknown pretraining exposure, broader research search
and neural training variance. Seed sensitivity is reported separately.
