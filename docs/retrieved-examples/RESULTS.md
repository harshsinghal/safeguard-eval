# Retrieved examples with fixed decision rules

All results concern the same 1,699 WildGuardTest harmful-prompt labels. No score calibration or threshold search.

| Model | Condition | Accuracy | Balanced accuracy | False blocks / 945 | Misses / 754 | Validation nominated |
|---|---|---:|---:|---:|---:|---|
| policylm | policy_only | 86.70% | 86.26% | 93 | 133 | yes |
| policylm | fixed_four | 86.87% | 87.02% | 135 | 88 |  |
| policylm | nearest_four | 84.34% | 84.91% | 190 | 76 |  |
| policylm | balanced_nearest | 84.46% | 84.95% | 183 | 81 |  |
| shieldstral | policy_only | 90.82% | 90.42% | 57 | 99 | yes |
| shieldstral | fixed_four | 89.94% | 89.48% | 61 | 110 |  |
| shieldstral | nearest_four | 89.70% | 89.52% | 84 | 91 |  |
| shieldstral | balanced_nearest | 89.94% | 89.68% | 76 | 95 |  |
| kev | policy_only | 87.52% | 87.20% | 94 | 118 |  |
| kev | fixed_four | 87.11% | 87.11% | 122 | 97 |  |
| kev | nearest_four | 88.17% | 88.29% | 121 | 80 |  |
| kev | balanced_nearest | 88.11% | 88.21% | 120 | 82 | yes |
| jev | policy_only | 89.29% | 89.06% | 84 | 98 |  |
| jev | fixed_four | 88.88% | 88.49% | 76 | 113 |  |
| jev | nearest_four | 89.46% | 89.24% | 83 | 96 |  |
| jev | balanced_nearest | 89.76% | 89.56% | 82 | 92 | yes |
| knn | knn | 70.04% | 71.18% | 368 | 141 |  |

## Paired changes

| Model | Comparison | Accuracy change (pp) | 95% interval (pp) | Corrected | Introduced |
|---|---|---:|---|---:|---:|
| policylm | nearest_four minus policy_only | -2.35 | -3.94 to -0.82 | 66 | 106 |
| policylm | nearest_four minus fixed_four | -2.53 | -3.83 to -1.35 | 40 | 83 |
| policylm | fixed_four minus policy_only | +0.18 | -1.00 to +1.35 | 51 | 48 |
| policylm | balanced_nearest minus policy_only | -2.24 | -3.71 to -0.71 | 63 | 101 |
| policylm | balanced_nearest minus nearest_four | +0.12 | -0.77 to +1.00 | 32 | 30 |
| shieldstral | nearest_four minus policy_only | -1.12 | -1.94 to -0.35 | 13 | 32 |
| shieldstral | nearest_four minus fixed_four | -0.24 | -1.12 to +0.65 | 26 | 30 |
| shieldstral | fixed_four minus policy_only | -0.88 | -1.53 to -0.29 | 9 | 24 |
| shieldstral | balanced_nearest minus policy_only | -0.88 | -1.59 to -0.18 | 13 | 28 |
| shieldstral | balanced_nearest minus nearest_four | +0.24 | -0.35 to +0.82 | 16 | 12 |
| kev | nearest_four minus policy_only | +0.65 | -0.53 to +1.82 | 60 | 49 |
| kev | nearest_four minus fixed_four | +1.06 | +0.18 to +2.00 | 43 | 25 |
| kev | fixed_four minus policy_only | -0.41 | -1.47 to +0.59 | 38 | 45 |
| kev | balanced_nearest minus policy_only | +0.59 | -0.47 to +1.71 | 52 | 42 |
| kev | balanced_nearest minus nearest_four | -0.06 | -0.82 to +0.71 | 22 | 23 |
| jev | nearest_four minus policy_only | +0.18 | -0.65 to +1.00 | 27 | 24 |
| jev | nearest_four minus fixed_four | +0.59 | -0.29 to +1.47 | 33 | 23 |
| jev | fixed_four minus policy_only | -0.41 | -1.12 to +0.29 | 15 | 22 |
| jev | balanced_nearest minus policy_only | +0.47 | -0.35 to +1.24 | 30 | 22 |
| jev | balanced_nearest minus nearest_four | +0.29 | -0.24 to +0.82 | 13 | 8 |

Intervals are descriptive and unadjusted. Prior benchmark reuse, training-label noise, model-specific example formats and unknown checkpoint exposure limit generalization.
