# Prompt-injection benchmark: results

These are separate test collections, not a pooled security score. Every model uses the policy selected on validation; the brief baseline is retained for comparison. Model weights and decision rules are fixed.

## Why each policy was selected

These are validation results on 256 development examples, not held-out test scores. Each cell is the equal-source mean balanced accuracy. Selection and tie-breaking rules were registered before these results.

| Model | Brief | Structured | Structured + fitting examples | Selected |
|---|---:|---:|---:|---|
| PolicyLM 1.7B | 88.28% | 91.41% | 94.14% | examples |
| Shieldstral 3B | 70.31% | 76.17% | 75.78% | structured |
| GPT-OSS Safeguard 20B | 71.88% | 72.27% | 77.34% | examples |
| Kev 4B | 84.38% | 82.81% | 56.25% | brief |
| Clef-Flash | 85.55% | 81.64% | 82.03% | brief |
| Jev 1.14 | 80.86% | 83.59% | 84.38% | examples |

The final tests below compare only the brief baseline and the policy selected here. No candidate was promoted because of its test score.

## xTRam1 Safe-Guard: 2,060 original test examples

| Model | Selected policy | Accuracy | Balanced accuracy | Macro F1 | MCC | False blocks | Missed attacks | Unresolved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | examples | 95.92% | 95.32% | 95.28% | 0.906 | 43/1410 (3.05%) | 41/650 (6.31%) | 0 |
| Shieldstral 3B | structured | 90.00% | 84.32% | 87.24% | 0.771 | 4/1410 (0.28%) | 202/650 (31.08%) | 0 |
| GPT-OSS Safeguard 20B | examples | 92.52% | 88.24% | 90.97% | — | 2/1410 (0.14%) | 136/650 (20.92%) | 16 |
| Kev 4B | brief | 95.87% | 93.50% | 95.04% | 0.905 | 1/1410 (0.07%) | 84/650 (12.92%) | 0 |
| Clef-Flash | brief | 97.04% | 95.35% | 96.48% | 0.932 | 1/1410 (0.07%) | 60/650 (9.23%) | 0 |
| Jev 1.14 | examples | 93.79% | 90.15% | 92.37% | 0.858 | 0/1410 (0.00%) | 128/650 (19.69%) | 0 |

| Model | Brief policy BA | Selected policy BA | Change (points) | Paired 95% interval (points) |
|---|---:|---:|---:|---:|
| PolicyLM 1.7B | 95.52% | 95.32% | -0.20 | [-1.21, +0.70] |
| Shieldstral 3B | 71.66% | 84.32% | +12.66 | [+10.91, +14.40] |
| GPT-OSS Safeguard 20B | 80.15% | 88.24% | +8.08 | [+6.50, +9.69] |
| Kev 4B | 93.50% | 93.50% | +0.00 | [+0.00, +0.00] |
| Clef-Flash | 95.35% | 95.35% | +0.00 | [+0.00, +0.00] |
| Jev 1.14 | 82.85% | 90.15% | +7.31 | [+5.79, +8.84] |

## Deepset: 116 original test examples

| Model | Selected policy | Accuracy | Balanced accuracy | Macro F1 | MCC | False blocks | Missed attacks | Unresolved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | examples | 75.86% | 76.67% | 74.78% | 0.596 | 0/56 (0.00%) | 28/60 (46.67%) | 0 |
| Shieldstral 3B | structured | 62.07% | 63.33% | 56.95% | 0.386 | 0/56 (0.00%) | 44/60 (73.33%) | 0 |
| GPT-OSS Safeguard 20B | examples | 59.48% | 60.77% | 53.70% | 0.321 | 1/56 (1.79%) | 46/60 (76.67%) | 0 |
| Kev 4B | brief | 68.10% | 69.17% | 65.29% | 0.480 | 0/56 (0.00%) | 37/60 (61.67%) | 0 |
| Clef-Flash | brief | 66.38% | 67.50% | 63.01% | 0.454 | 0/56 (0.00%) | 39/60 (65.00%) | 0 |
| Jev 1.14 | examples | 72.41% | 73.33% | 70.71% | 0.545 | 0/56 (0.00%) | 32/60 (53.33%) | 0 |

| Model | Brief policy BA | Selected policy BA | Change (points) | Paired 95% interval (points) |
|---|---:|---:|---:|---:|
| PolicyLM 1.7B | 71.67% | 76.67% | +5.00 | [+0.86, +10.00] |
| Shieldstral 3B | 61.67% | 63.33% | +1.67 | [+0.00, +4.55] |
| GPT-OSS Safeguard 20B | 61.67% | 60.77% | -0.89 | [-4.16, +1.75] |
| Kev 4B | 69.17% | 69.17% | +0.00 | [+0.00, +0.00] |
| Clef-Flash | 67.50% | 67.50% | +0.00 | [+0.00, +0.00] |
| Jev 1.14 | 74.17% | 73.33% | -0.83 | [-2.83, +0.00] |

## NotInject: 339 benign lookalikes

| Model | Benign allow rate | False blocks | Unresolved | Brief false-block rate | Selected false-block rate |
|---|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | 92.33% | 26/339 | 0 | 6.78% | 7.67% |
| Shieldstral 3B | 99.71% | 1/339 | 0 | 0.29% | 0.29% |
| GPT-OSS Safeguard 20B | 98.23% | 4/339 | 2 | 0.88% | 1.18% |
| Kev 4B | 97.35% | 9/339 | 0 | 2.65% | 2.65% |
| Clef-Flash | 97.05% | 10/339 | 0 | 2.95% | 2.95% |
| Jev 1.14 | 99.12% | 3/339 | 0 | 0.88% | 0.88% |

## JailbreakBench: 182 released attack attempts

| Model | Overall detection | GCG detection (100) | PAIR detection (82) | Allowed attempts | Unresolved | Brief overall detection |
|---|---:|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | 94.51% | 97.00% | 91.46% | 10 | 0 | 84.07% |
| Shieldstral 3B | 90.11% | 89.00% | 91.46% | 18 | 0 | 42.86% |
| GPT-OSS Safeguard 20B | 93.96% | 96.00% | 91.46% | 9 | 2 | 74.73% |
| Kev 4B | 89.56% | 92.00% | 86.59% | 19 | 0 | 89.56% |
| Clef-Flash | 91.21% | 91.00% | 91.46% | 16 | 0 | 91.21% |
| Jev 1.14 | 50.00% | 62.00% | 35.37% | 91 | 0 | 31.32% |

NotInject has only benign examples, and JBB only attack attempts. Neither receives a balanced-accuracy or macro-F1 score. A detector that blocks everything would catch every JBB attempt while failing NotInject completely. JBB rates describe detection of released attempts, not prevention of downstream attacks.

## Interpretation and uncertainty

Balanced accuracy gives equal weight to attack recall and benign allow rate. Accuracy retains the published class mixture. Unresolved outputs remain in denominators and cannot become artificial correct blocks; MCC is unavailable when predictions are unresolved. False-block and missed-attack columns count actual BLOCK/ALLOW errors; unresolved cases are shown separately.

Intervals use 2,000 paired bootstrap draws of related-text groups. An interval spanning zero does not establish a directional improvement. These are exploratory comparisons without multiplicity correction. The small deepset test is particularly uncertain. Source annotations can be ambiguous without the original governing instructions; scores measure agreement with those labels.

See the machine-readable summary for all baseline/selected metrics, absolute intervals, NotInject category/trigger slices, JBB method/category slices, and prespecified text-format slices. Character-format slices are text properties, not independently labeled attack categories.
