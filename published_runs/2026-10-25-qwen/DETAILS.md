# Complete result tables

All figures below are computed from the archived predictions. Accuracy and F1 are percentages. Differences and intervals use percentage points. Intervals are exploratory, unadjusted and conditional on the chosen prompts.

## Test: initial, shared and selected prompts

| Qwen model | Initial accuracy | Shared accuracy | Selected accuracy | Selected harmful F1 | Selected policy |
|---|---|---|---|---|---|
| Qwen3.5-2B | 79.93 | 83.05 | 83.05 | 81.49 | wg-p2-boundary-checklist |
| Qwen3.5-4B | 85.64 | 86.82 | 87.58 | 85.87 | wg-p1-concrete-harm |
| Qwen3.5-9B | 89.05 | 89.29 | 89.58 | 88.11 | qwen-9b-p3-social-and-sensitive-boundaries |
| Qwen3.5-27B | 89.41 | 90.64 | 91.29 | 90.24 | wg-p1-concrete-harm |
| Qwen3.5-35B-A3B | 90.29 | 90.11 | 90.29 | 89.07 | qwen-35b-a3b-p4-compact-content-and-purpose |

## Selected prompts: error tradeoffs and prompt-tuning gain

| Model | False blocks | Missed harms | Output errors | Harm recall | False-block rate | Gain vs initial | Paired 95% interval |
|---|---|---|---|---|---|---|---|
| Qwen3.5-2B | 168 | 120 | 0 | 84.08 | 17.78 | 3.12 | [1.71, 4.53] |
| Qwen3.5-4B | 98 | 113 | 0 | 85.01 | 10.37 | 1.94 | [1.06, 2.77] |
| Qwen3.5-9B | 79 | 98 | 0 | 87.00 | 8.36 | 0.53 | [-0.18, 1.24] |
| Qwen3.5-27B | 78 | 70 | 0 | 90.72 | 8.25 | 1.88 | [1.00, 2.83] |
| Qwen3.5-35B-A3B | 83 | 82 | 0 | 89.12 | 8.78 | 0.00 | [-0.88, 0.88] |

## All registered nearby-size comparisons

| Qwen | Specialist | Prompt comparison | Qwen accuracy | Specialist accuracy | Difference | Paired 95% interval | Qwen-only / specialist-only correct |
|---|---|---|---|---|---|---|---|
| Qwen3.5-2B | PolicyLM-1.7B | initial | 79.93 | 85.05 | -5.12 | [-7.00, -3.18] | 98 / 185 |
| Qwen3.5-2B | PolicyLM-1.7B | shared | 83.05 | 87.17 | -4.12 | [-5.83, -2.41] | 79 / 149 |
| Qwen3.5-2B | PolicyLM-1.7B | selected | 83.05 | 86.82 | -3.77 | [-5.59, -1.94] | 89 / 153 |
| Qwen3.5-4B | Shieldstral-3B | initial | 85.64 | 87.93 | -2.30 | [-4.00, -0.65] | 83 / 122 |
| Qwen3.5-4B | Shieldstral-3B | shared | 86.82 | 90.82 | -4.00 | [-5.41, -2.59] | 40 / 108 |
| Qwen3.5-4B | Shieldstral-3B | selected | 87.58 | 90.82 | -3.24 | [-4.59, -1.88] | 40 / 95 |
| Qwen3.5-9B | WildGuard-7B | initial | 89.05 | 90.35 | -1.29 | [-2.65, 0.12] | 60 / 82 |
| Qwen3.5-9B | WildGuard-7B | shared | 89.29 | 90.35 | -1.06 | [-2.47, 0.29] | 61 / 79 |
| Qwen3.5-9B | WildGuard-7B | selected | 89.58 | 90.35 | -0.77 | [-2.18, 0.59] | 63 / 76 |
| Qwen3.5-27B | CoPE-B-A4B | initial | 89.41 | 90.46 | -1.06 | [-2.41, 0.29] | 60 / 78 |
| Qwen3.5-27B | CoPE-B-A4B | shared | 90.64 | 90.41 | 0.24 | [-1.06, 1.53] | 64 / 60 |
| Qwen3.5-27B | CoPE-B-A4B | selected | 91.29 | 90.76 | 0.53 | [-0.53, 1.59] | 46 / 37 |
| Qwen3.5-27B | Safeguard-20B | initial | 89.41 | 89.82 | -0.41 | [-1.77, 0.88] | 62 / 69 |
| Qwen3.5-27B | Safeguard-20B | shared | 90.64 | 89.64 | 1.00 | [-0.35, 2.35] | 75 / 58 |
| Qwen3.5-27B | Safeguard-20B | selected | 91.29 | 89.64 | 1.65 | [0.41, 2.94] | 76 / 48 |
| Qwen3.5-35B-A3B | CoPE-B-A4B | initial | 90.29 | 90.46 | -0.18 | [-1.41, 1.12] | 58 / 61 |
| Qwen3.5-35B-A3B | CoPE-B-A4B | shared | 90.11 | 90.41 | -0.29 | [-1.53, 1.00] | 59 / 64 |
| Qwen3.5-35B-A3B | CoPE-B-A4B | selected | 90.29 | 90.76 | -0.47 | [-1.71, 0.71] | 53 / 61 |
| Qwen3.5-35B-A3B | Safeguard-20B | initial | 90.29 | 89.82 | 0.47 | [-0.77, 1.82] | 65 / 57 |
| Qwen3.5-35B-A3B | Safeguard-20B | shared | 90.11 | 89.64 | 0.47 | [-0.94, 1.82] | 74 / 66 |
| Qwen3.5-35B-A3B | Safeguard-20B | selected | 90.29 | 89.64 | 0.65 | [-0.77, 2.06] | 80 / 69 |

## Validation-selected score thresholds

These are separate controls. Primary results above use the free-generated label. Errors remain errors.

| Model | Policy | Threshold | Free-label accuracy | Threshold accuracy | Threshold harmful F1 |
|---|---|---|---|---|---|
| Qwen3.5-2B | wg-p0-taxonomy | 0.9 | 79.93 | 82.93 | 80.90 |
| Qwen3.5-2B | wg-p2-boundary-checklist | 0.6 | 83.05 | 83.46 | 81.48 |
| Qwen3.5-4B | wg-p0-taxonomy | 0.57 | 85.64 | 85.46 | 82.72 |
| Qwen3.5-4B | wg-p1-concrete-harm | 0.43 | 87.58 | 86.76 | 85.40 |
| Qwen3.5-4B | wg-p2-boundary-checklist | 0.46 | 86.82 | 86.82 | 85.11 |
| Qwen3.5-9B | wg-p0-taxonomy | 0.68 | 89.05 | 88.76 | 86.91 |
| Qwen3.5-9B | wg-p2-boundary-checklist | 0.51 | 89.29 | 89.29 | 87.75 |
| Qwen3.5-9B | qwen-9b-p3-social-and-sensitive-boundaries | 0.51 | 89.58 | 89.58 | 88.11 |
| Qwen3.5-27B | wg-p0-taxonomy | 0.97 | 89.41 | 90.23 | 88.47 |
| Qwen3.5-27B | wg-p1-concrete-harm | 0.86 | 91.29 | 91.17 | 89.77 |
| Qwen3.5-27B | wg-p2-boundary-checklist | 0.93 | 90.64 | 91.35 | 89.97 |
| Qwen3.5-35B-A3B | wg-p0-taxonomy | 0.57 | 90.29 | 90.41 | 89.10 |
| Qwen3.5-35B-A3B | wg-p2-boundary-checklist | 0.66 | 90.11 | 90.23 | 88.60 |
| Qwen3.5-35B-A3B | qwen-35b-a3b-p4-compact-content-and-purpose | 0.57 | 90.29 | 90.41 | 88.99 |

## Comparisons after each available validation threshold

WildGuard and Safeguard retain their historical explicit labels because no matching historical score control exists.

| Qwen | Specialist | Role | Qwen cutoff | Specialist cutoff | Qwen accuracy | Specialist accuracy | Difference | Paired 95% interval |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-2B | PolicyLM-1.7B | initial | 0.9 | 0.54 | 82.93 | 85.11 | -2.18 | [-3.94, -0.35] |
| Qwen3.5-2B | PolicyLM-1.7B | shared | 0.6 | 0.32 | 83.46 | 85.34 | -1.88 | [-3.71, -0.06] |
| Qwen3.5-2B | PolicyLM-1.7B | selected | 0.6 | 0.44 | 83.46 | 86.52 | -3.06 | [-4.83, -1.29] |
| Qwen3.5-4B | Shieldstral-3B | initial | 0.57 | 0.14 | 85.46 | 90.11 | -4.65 | [-6.24, -3.00] |
| Qwen3.5-4B | Shieldstral-3B | shared | 0.46 | 0.46 | 86.82 | 90.82 | -4.00 | [-5.41, -2.59] |
| Qwen3.5-4B | Shieldstral-3B | selected | 0.43 | 0.5 | 86.76 | 90.82 | -4.06 | [-5.47, -2.71] |
| Qwen3.5-9B | WildGuard-7B | initial | 0.68 | explicit | 88.76 | 90.35 | -1.59 | [-2.94, -0.24] |
| Qwen3.5-9B | WildGuard-7B | shared | 0.51 | explicit | 89.29 | 90.35 | -1.06 | [-2.47, 0.29] |
| Qwen3.5-9B | WildGuard-7B | selected | 0.51 | explicit | 89.58 | 90.35 | -0.77 | [-2.18, 0.59] |
| Qwen3.5-27B | CoPE-B-A4B | initial | 0.97 | 0.5 | 90.23 | 90.46 | -0.24 | [-1.29, 0.77] |
| Qwen3.5-27B | CoPE-B-A4B | shared | 0.93 | 0.06 | 91.35 | 90.58 | 0.77 | [-0.18, 1.77] |
| Qwen3.5-27B | CoPE-B-A4B | selected | 0.86 | 0.08 | 91.17 | 90.94 | 0.24 | [-0.65, 1.18] |
| Qwen3.5-27B | Safeguard-20B | initial | 0.97 | explicit | 90.23 | 89.82 | 0.41 | [-0.82, 1.59] |
| Qwen3.5-27B | Safeguard-20B | shared | 0.93 | explicit | 91.35 | 89.64 | 1.71 | [0.53, 2.94] |
| Qwen3.5-27B | Safeguard-20B | selected | 0.86 | explicit | 91.17 | 89.64 | 1.53 | [0.29, 2.77] |
| Qwen3.5-35B-A3B | CoPE-B-A4B | initial | 0.57 | 0.5 | 90.41 | 90.46 | -0.06 | [-1.29, 1.18] |
| Qwen3.5-35B-A3B | CoPE-B-A4B | shared | 0.66 | 0.06 | 90.23 | 90.58 | -0.35 | [-1.59, 0.82] |
| Qwen3.5-35B-A3B | CoPE-B-A4B | selected | 0.57 | 0.08 | 90.41 | 90.94 | -0.53 | [-1.71, 0.59] |
| Qwen3.5-35B-A3B | Safeguard-20B | initial | 0.57 | explicit | 90.41 | 89.82 | 0.59 | [-0.71, 1.94] |
| Qwen3.5-35B-A3B | Safeguard-20B | shared | 0.66 | explicit | 90.23 | 89.64 | 0.59 | [-0.77, 1.94] |
| Qwen3.5-35B-A3B | Safeguard-20B | selected | 0.57 | explicit | 90.41 | 89.64 | 0.77 | [-0.65, 2.12] |

## Prompt changes versus changing only the initial cutoff

Secondary paired contrasts were added during final inference; prompts, cutoffs and primary outcomes stayed frozen.

| Model | Initial calibrated accuracy | Selected free-label accuracy | Difference | Paired 95% interval | Selected calibrated accuracy |
|---|---|---|---|---|---|
| Qwen3.5-2B | 82.93 | 83.05 | 0.12 | [-1.06, 1.12] | 83.46 |
| Qwen3.5-4B | 85.46 | 87.58 | 2.12 | [1.12, 3.12] | 86.76 |
| Qwen3.5-9B | 88.76 | 89.58 | 0.82 | [0.00, 1.65] | 89.58 |
| Qwen3.5-27B | 90.23 | 91.29 | 1.06 | [0.00, 2.12] | 91.17 |
| Qwen3.5-35B-A3B | 90.41 | 90.29 | -0.12 | [-1.00, 0.77] | 90.41 |

## All candidate fitting and validation scores

Each model has the same five-candidate budget. Individual validation mistakes were not used for editing.

| Model | Policy | Fitting accuracy (1,024) | Validation accuracy (512) | Selected |
|---|---|---|---|---|
| Qwen3.5-2B | wg-p0-taxonomy | 82.91 | 84.18 |  |
| Qwen3.5-2B | wg-p1-concrete-harm | 83.79 | 86.72 |  |
| Qwen3.5-2B | wg-p2-boundary-checklist | 86.04 | 87.70 | yes |
| Qwen3.5-4B | wg-p0-taxonomy | 90.33 | 89.45 |  |
| Qwen3.5-4B | wg-p1-concrete-harm | 91.80 | 91.02 | yes |
| Qwen3.5-4B | wg-p2-boundary-checklist | 91.11 | 90.43 |  |
| Qwen3.5-9B | wg-p0-taxonomy | 92.38 | 92.38 |  |
| Qwen3.5-9B | wg-p1-concrete-harm | 93.16 | 93.36 |  |
| Qwen3.5-9B | wg-p2-boundary-checklist | 91.60 | 93.75 |  |
| Qwen3.5-27B | wg-p0-taxonomy | 92.48 | 91.80 |  |
| Qwen3.5-27B | wg-p1-concrete-harm | 94.04 | 94.53 | yes |
| Qwen3.5-27B | wg-p2-boundary-checklist | 93.16 | 93.55 |  |
| Qwen3.5-35B-A3B | wg-p0-taxonomy | 92.87 | 92.97 |  |
| Qwen3.5-35B-A3B | wg-p1-concrete-harm | 92.87 | 94.53 |  |
| Qwen3.5-35B-A3B | wg-p2-boundary-checklist | 93.07 | 93.75 |  |
| Qwen3.5-2B | qwen-2b-p3-grounded-boundaries | 84.77 | 86.91 |  |
| Qwen3.5-2B | qwen-2b-p4-compact-evidence | 83.69 | 85.94 |  |
| Qwen3.5-4B | qwen-4b-p3-deliverable-and-exceptions | 89.26 | 89.65 |  |
| Qwen3.5-4B | qwen-4b-p4-content-and-request | 89.55 | 88.87 |  |
| Qwen3.5-9B | qwen-9b-p3-social-and-sensitive-boundaries | 92.29 | 94.14 | yes |
| Qwen3.5-9B | qwen-9b-p4-compact-substance | 91.70 | 92.77 |  |
| Qwen3.5-27B | qwen-27b-p3-evidence-and-sensitive-data | 93.16 | 92.77 |  |
| Qwen3.5-27B | qwen-27b-p4-compact-substance-and-endorsement | 92.38 | 92.58 |  |
| Qwen3.5-35B-A3B | qwen-35b-a3b-p3-action-object-boundaries | 91.31 | 92.38 |  |
| Qwen3.5-35B-A3B | qwen-35b-a3b-p4-compact-content-and-purpose | 93.16 | 94.53 | yes |

## Internal audit (512 rows)

The audit was frozen and evaluated after selection; it was not used to revise prompts. It comes from the training source population and uses its labels.

| Model | Role | Accuracy | Harmful F1 | Output errors |
|---|---|---|---|---|
| Qwen3.5-2B | initial | 80.27 | 83.25 | 0 |
| Qwen3.5-2B | shared | 82.23 | 83.78 | 0 |
| Qwen3.5-2B | selected | 82.23 | 83.78 | 0 |
| Qwen3.5-4B | initial | 88.48 | 89.29 | 0 |
| Qwen3.5-4B | shared | 88.87 | 89.54 | 0 |
| Qwen3.5-4B | selected | 88.28 | 89.13 | 0 |
| Qwen3.5-9B | initial | 90.82 | 91.44 | 0 |
| Qwen3.5-9B | shared | 91.02 | 91.54 | 0 |
| Qwen3.5-9B | selected | 91.80 | 92.34 | 0 |
| Qwen3.5-27B | initial | 90.82 | 91.65 | 0 |
| Qwen3.5-27B | shared | 91.02 | 91.81 | 0 |
| Qwen3.5-27B | selected | 91.60 | 92.25 | 0 |
| Qwen3.5-35B-A3B | initial | 93.75 | 94.14 | 0 |
| Qwen3.5-35B-A3B | shared | 93.75 | 94.20 | 0 |
| Qwen3.5-35B-A3B | selected | 93.16 | 93.65 | 0 |

## Selected prompts: vanilla and adversarial test slices

These are source-provided prompt styles, not measures of downstream attack success.

| Model | Adversarial source flag | Rows | Accuracy | Harmful F1 |
|---|---|---|---|---|
| Qwen3.5-2B | False | 903 | 87.82 | 86.75 |
| Qwen3.5-2B | True | 796 | 77.64 | 75.48 |
| Qwen3.5-4B | False | 903 | 91.47 | 90.01 |
| Qwen3.5-4B | True | 796 | 83.17 | 81.44 |
| Qwen3.5-9B | False | 903 | 93.36 | 92.44 |
| Qwen3.5-9B | True | 796 | 85.30 | 83.17 |
| Qwen3.5-27B | False | 903 | 95.02 | 94.49 |
| Qwen3.5-27B | True | 796 | 87.06 | 85.26 |
| Qwen3.5-35B-A3B | False | 903 | 94.13 | 93.42 |
| Qwen3.5-35B-A3B | True | 796 | 85.93 | 84.09 |

## Repeated-input diagnostic

Pilot and search reuse some identical requests under different batch contexts. This diagnostic has no controlled repetition or seed sweep.

| Model | Common rows | Identical requests | Changed decisions |
|---|---|---|---|
| Qwen3.5-2B | 256 | 256 | 1 |
| Qwen3.5-4B | 256 | 256 | 0 |
| Qwen3.5-9B | 256 | 256 | 0 |
| Qwen3.5-27B | 256 | 256 | 0 |
| Qwen3.5-35B-A3B | 256 | 256 | 4 |

Full category metrics, all confusion matrices, paired discordances and calibration controls are in [analysis.json](analysis.json). Exact policies, predictions and run metadata are indexed in [run-index.json](run-index.json).
