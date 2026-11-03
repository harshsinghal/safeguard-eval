# Malicious artifact screening: results

All configurations were selected on validation and frozen before any test inference. The two tasks have different labels and populations; do not average them into one security score. See [methods](METHODS.md), [selection record](preparation/README.md), and [reproduction](RUNNING.md).

Balanced accuracy averages malicious recall and benign specificity. False blocks count benign artifacts labeled malicious; misses count malicious artifacts labeled benign. Intervals below are 95% grouped bootstrap intervals, not guarantees for new deployments. See the [metric definitions](../../docs/leaderboard/METRICS.md).

## Code files: 160 held-out examples

80 benign and 80 malicious, across 101 package/similarity groups.

| System | Family | Selected | Accuracy | Balanced accuracy [95% CI] | Macro F1 | MCC | False blocks | Misses | Unresolved |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Fine-tuned Liquid 350M | Trained encoder | lr5e-05-epoch3 | 91.25% | 91.25% [86.48 to 95.76] | 91.23% | 0.829 | 3 | 11 | 0 |
| Jev-1.14 | Decision API | brief | 90.00% | 90.00% [84.90 to 95.14] | 89.90% | 0.816 | 0 | 16 | 0 |
| Clef-Flash | Decision | structured | 88.75% | 88.75% [83.82 to 93.90] | 88.61% | 0.795 | 0 | 18 | 0 |
| Character TF-IDF + logistic regression | Trained lexical | C10 | 88.12% | 88.12% [82.50 to 93.75] | 87.96% | 0.785 | 0 | 19 | 0 |
| PolicyLM-1.7B | Policy | evidence | 86.88% | 86.88% [81.61 to 92.14] | 86.83% | 0.742 | 6 | 15 | 0 |
| Qwen3.5-4B | General LLM | brief | 86.88% | 86.88% [81.69 to 92.47] | 86.64% | 0.764 | 0 | 21 | 0 |
| Kev-4B | Decision | evidence | 78.75% | 78.75% [71.25 to 87.86] | 77.75% | 0.635 | 0 | 34 | 0 |
| Shieldstral-1.0-3B | Policy | structured | 76.25% | 76.25% [69.14 to 84.64] | 74.98% | 0.588 | 1 | 37 | 0 |

### Policy changes on the same held-out examples

Only brief and validation-selected policies were run on test. The selected variant is not chosen again from these test results. When validation retained brief, its predictions are reused; otherwise, a zero aggregate change can still hide different individual decisions. Positive differences favor the selected policy; changes are percentage points.

| Model | Brief balanced accuracy | Selected balanced accuracy | Change [paired 95% CI] | False blocks: brief → selected | Misses: brief → selected |
|---|---:|---:|---:|---:|---:|
| Jev-1.14 | 90.00% | 90.00% | +0.00 [0.00 to 0.00] | 0 → 0 | 16 → 16 |
| Clef-Flash | 88.12% | 88.75% | +0.62 [-1.52 to 2.60] | 0 → 0 | 19 → 18 |
| PolicyLM-1.7B | 70.00% | 86.88% | +16.88 [9.45 to 24.11] | 48 → 6 | 0 → 15 |
| Qwen3.5-4B | 86.88% | 86.88% | +0.00 [0.00 to 0.00] | 0 → 0 | 21 → 21 |
| Kev-4B | 78.75% | 78.75% | +0.00 [-1.81 to 1.85] | 0 → 0 | 34 → 34 |
| Shieldstral-1.0-3B | 74.38% | 76.25% | +1.87 [-1.30 to 5.30] | 0 → 1 | 41 → 37 |

### Input-view slices

Clipped views keep the first 6,000 and last 2,000 source bytes; the original label stays unchanged. Differences between these slices are descriptive: length and content also differ, so this is not a causal estimate of clipping damage.

| System | Complete view: n / balanced accuracy | Clipped view: n / balanced accuracy | Malicious recall | Benign specificity |
|---|---:|---:|---:|---:|
| Fine-tuned Liquid 350M | 122 / 95.13% | 38 / 77.03% | 86.25% | 96.25% |
| Jev-1.14 | 122 / 91.27% | 38 / 85.29% | 80.00% | 100.00% |
| Clef-Flash | 122 / 88.89% | 38 / 88.24% | 77.50% | 100.00% |
| Character TF-IDF + logistic regression | 122 / 88.89% | 38 / 85.29% | 76.25% | 100.00% |
| PolicyLM-1.7B | 122 / 88.73% | 38 / 81.09% | 81.25% | 92.50% |
| Qwen3.5-4B | 122 / 87.30% | 38 / 85.29% | 73.75% | 100.00% |
| Kev-4B | 122 / 78.57% | 38 / 79.41% | 57.50% | 100.00% |
| Shieldstral-1.0-3B | 122 / 76.14% | 38 / 76.47% | 53.75% | 98.75% |

## Agent skills: 1,384 source-held-out examples

545 benign and 839 malicious; source holdout is not an unseen-family holdout.

| System | Family | Selected | Accuracy | Balanced accuracy [95% CI] | Macro F1 | MCC | False blocks | Misses | Unresolved |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Character TF-IDF + logistic regression | Trained lexical | C10 | 73.92% | 70.19% [66.53 to 73.19] | 70.85% | 0.439 | 258 | 103 | 0 |
| Fine-tuned Liquid 350M | Trained encoder | lr5e-05-epoch3 | 68.86% | 65.06% [60.79 to 68.42] | 65.37% | 0.325 | 288 | 143 | 0 |
| PolicyLM-1.7B | Policy | structured | 55.27% | 61.86% [57.57 to 65.36] | 53.80% | 0.282 | 39 | 580 | 0 |
| Jev-1.14 | Decision API | structured | 48.12% | 57.21% [54.82 to 60.35] | 42.75% | 0.249 | 0 | 718 | 0 |
| Clef-Flash | Decision | structured | 45.74% | 55.24% [52.81 to 58.45] | 39.10% | 0.210 | 0 | 751 | 0 |
| Qwen3.5-4B | General LLM | structured | 44.44% | 54.17% [51.93 to 57.15] | 37.02% | 0.186 | 0 | 769 | 0 |
| Kev-4B | Decision | structured | 43.71% | 53.51% [51.46 to 56.34] | 35.98% | 0.163 | 2 | 777 | 0 |
| Shieldstral-1.0-3B | Policy | structured | 42.34% | 52.44% [50.90 to 54.72] | 33.53% | 0.141 | 0 | 798 | 0 |

### Policy changes on the same held-out examples

Only brief and validation-selected policies were run on test. The selected variant is not chosen again from these test results. When validation retained brief, its predictions are reused; otherwise, a zero aggregate change can still hide different individual decisions. Positive differences favor the selected policy; changes are percentage points.

| Model | Brief balanced accuracy | Selected balanced accuracy | Change [paired 95% CI] | False blocks: brief → selected | Misses: brief → selected |
|---|---:|---:|---:|---:|---:|
| PolicyLM-1.7B | 53.41% | 61.86% | +8.45 [3.56 to 12.35] | 33 → 39 | 731 → 580 |
| Jev-1.14 | 57.75% | 57.21% | -0.54 [-1.21 to -0.06] | 0 → 0 | 709 → 718 |
| Clef-Flash | 54.65% | 55.24% | +0.60 [0.22 to 1.11] | 0 → 0 | 761 → 751 |
| Qwen3.5-4B | 54.17% | 54.17% | +0.00 [-0.64 to 0.47] | 0 → 0 | 769 → 769 |
| Kev-4B | 52.86% | 53.51% | +0.65 [0.01 to 1.53] | 0 → 2 | 791 → 777 |
| Shieldstral-1.0-3B | 51.01% | 52.44% | +1.43 [0.53 to 2.71] | 0 → 0 | 822 → 798 |

### Input-view slices

Clipped views keep the first 6,000 and last 2,000 source bytes; the original label stays unchanged. Differences between these slices are descriptive: length and content also differ, so this is not a causal estimate of clipping damage.

| System | Complete view: n / balanced accuracy | Clipped view: n / balanced accuracy | Malicious recall | Benign specificity |
|---|---:|---:|---:|---:|
| Character TF-IDF + logistic regression | 986 / 69.55% | 398 / 71.91% | 87.72% | 52.66% |
| Fine-tuned Liquid 350M | 986 / 61.82% | 398 / 73.07% | 82.96% | 47.16% |
| PolicyLM-1.7B | 986 / 60.31% | 398 / 65.79% | 30.87% | 92.84% |
| Jev-1.14 | 986 / 59.00% | 398 / 52.72% | 14.42% | 100.00% |
| Clef-Flash | 986 / 57.33% | 398 / 50.00% | 10.49% | 100.00% |
| Qwen3.5-4B | 986 / 55.83% | 398 / 50.00% | 8.34% | 100.00% |
| Kev-4B | 986 / 54.91% | 398 / 50.00% | 7.39% | 99.63% |
| Shieldstral-1.0-3B | 986 / 53.42% | 398 / 50.00% | 4.89% | 100.00% |

## Interpretation limits

- Code uses a derived file-level subset. Of its 160 test labels, 99 are tagged as LLM annotations and 61 inherit a benign package label. Scores measure agreement with those labels, not independent confirmation that a program is malicious.
- Skill test sources are held out, but five structural families span fitting and test, covering 205 test records. The model sees skill text, not every auxiliary package file. Partial attack-category annotations support descriptive slices only.
- Liquid and TF-IDF use fitting labels and have one classifier per task. The six frozen models select among three prespecified policies on validation. Different label use and optimization budgets prevent an architecture-only causal conclusion.
- The evidence policy changes the decision boundary as well as adding detail: it asks for an observable behavior chain and allows a case when the visible artifact does not establish maliciousness. Gains cannot be attributed to formatting alone.
- Qwen uses thinking-disabled, constrained yes/no token-pair scoring. Native adapters and fixed cutoffs are part of each evaluated system. No new threshold tuning, calibration, retrieval or ensemble was added.
- Intervals are exploratory and unadjusted for multiple comparisons. They account for clustering within the sampled test, not annotation error, unknown upstream model exposure or fine-tuning seed variation. Liquid uses one seed. No artifacts were executed and no live agent was attacked.

Full source, label-source and partial-category slices are in [machine-readable results](../../published_runs/2026-11-03-malicious-artifacts/results.json). Predictions, policies, revisions and accounting are in the [frozen evidence bundle](../../published_runs/2026-11-03-malicious-artifacts/README.md).
