# Retrieval optimization results

Frozen validation selections on 1,699 reused WildGuardTest prompts; no output calibration.

| Model | Role | Accuracy | Balanced accuracy | False blocks | Misses | Mean examples |
|---|---|---:|---:|---:|---:|---:|
| policylm | policy_only | 86.70% | 86.26% | 93 | 133 | 0.00 |
| policylm | original_nearest | 84.34% | 84.91% | 190 | 76 | 4.00 |
| policylm | format_selected | 84.58% | 84.88% | 168 | 94 | 4.00 |
| policylm | retriever_selected | 85.40% | 85.20% | 123 | 125 | 4.00 |
| policylm | retrieval_selected | 86.52% | 86.19% | 103 | 126 | 4.00 |
| policylm | system_selected | 86.70% | 86.26% | 93 | 133 | 0.00 |
| shieldstral | policy_only | 90.82% | 90.42% | 57 | 99 | 0.00 |
| shieldstral | original_nearest | 89.70% | 89.52% | 84 | 91 | 4.00 |
| shieldstral | format_selected | 89.70% | 89.52% | 84 | 91 | 4.00 |
| shieldstral | retriever_selected | 89.64% | 89.36% | 77 | 99 | 4.00 |
| shieldstral | retrieval_selected | 89.94% | 89.68% | 76 | 95 | 4.00 |
| shieldstral | system_selected | 90.82% | 90.42% | 57 | 99 | 0.00 |
| kev | policy_only | 87.64% | 87.31% | 92 | 118 | 0.00 |
| kev | original_nearest | 87.99% | 88.12% | 123 | 81 | 4.00 |
| kev | format_selected | 87.99% | 88.12% | 123 | 81 | 4.00 |
| kev | retriever_selected | 87.99% | 88.12% | 123 | 81 | 4.00 |
| kev | retrieval_selected | 87.35% | 87.50% | 131 | 84 | 4.00 |
| kev | system_selected | 87.35% | 87.50% | 131 | 84 | 4.00 |
| jev | policy_only | 89.29% | 89.06% | 84 | 98 | 0.00 |
| jev | original_nearest | 89.46% | 89.24% | 83 | 96 | 4.00 |
| jev | format_selected | 89.46% | 89.26% | 84 | 95 | 4.00 |
| jev | retriever_selected | 89.46% | 89.26% | 84 | 95 | 4.00 |
| jev | retrieval_selected | 89.41% | 89.31% | 93 | 87 | 4.00 |
| jev | system_selected | 89.41% | 89.31% | 93 | 87 | 4.00 |

Roles that map to the same configuration reuse identical predictions; they are not independent trials.

## Paired accuracy changes

| Model | Contrast | Change (pp) | 95% interval (pp) | Corrected | Introduced |
|---|---|---:|---|---:|---:|
| policylm | policy_only -> system_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| policylm | policy_only -> retrieval_selected | -0.18 | -1.18 to +0.88 | 41 | 44 |
| policylm | original_nearest -> format_selected | +0.24 | -0.65 to +1.18 | 34 | 30 |
| policylm | format_selected -> retriever_selected | +0.82 | -0.41 to +2.06 | 64 | 50 |
| policylm | retriever_selected -> retrieval_selected | +1.12 | +0.06 to +2.24 | 52 | 33 |
| policylm | original_nearest -> retrieval_selected | +2.18 | +0.77 to +3.65 | 98 | 61 |
| shieldstral | policy_only -> system_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| shieldstral | policy_only -> retrieval_selected | -0.88 | -1.59 to -0.18 | 13 | 28 |
| shieldstral | original_nearest -> format_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| shieldstral | format_selected -> retriever_selected | -0.06 | -0.82 to +0.65 | 23 | 24 |
| shieldstral | retriever_selected -> retrieval_selected | +0.29 | -0.41 to +1.00 | 24 | 19 |
| shieldstral | original_nearest -> retrieval_selected | +0.24 | -0.35 to +0.82 | 16 | 12 |
| kev | policy_only -> system_selected | -0.29 | -1.47 to +0.88 | 48 | 53 |
| kev | policy_only -> retrieval_selected | -0.29 | -1.47 to +0.88 | 48 | 53 |
| kev | original_nearest -> format_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| kev | format_selected -> retriever_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| kev | retriever_selected -> retrieval_selected | -0.65 | -1.47 to +0.18 | 19 | 30 |
| kev | original_nearest -> retrieval_selected | -0.65 | -1.47 to +0.18 | 19 | 30 |
| jev | policy_only -> system_selected | +0.12 | -0.71 to +1.00 | 29 | 27 |
| jev | policy_only -> retrieval_selected | +0.12 | -0.71 to +1.00 | 29 | 27 |
| jev | original_nearest -> format_selected | +0.00 | -0.47 to +0.47 | 9 | 9 |
| jev | format_selected -> retriever_selected | +0.00 | +0.00 to +0.00 | 0 | 0 |
| jev | retriever_selected -> retrieval_selected | -0.06 | -0.82 to +0.65 | 20 | 21 |
| jev | original_nearest -> retrieval_selected | -0.06 | -0.82 to +0.71 | 22 | 23 |

Intervals are descriptive, unadjusted paired group bootstraps. Test reuse and validation search limit generalization.

## All validation configurations

| Model | Configuration | Accuracy | Balanced accuracy | False blocks | Misses |
|---|---|---:|---:|---:|---:|
| policylm | policy_only | 92.32% | 92.36% | 50 | 68 |
| policylm | original__e5__nearest4__short | 85.55% | 84.87% | 183 | 39 |
| policylm | original__e5__balanced4__short | 85.81% | 85.21% | 172 | 46 |
| policylm | native__e5__nearest4__short | 87.89% | 87.40% | 144 | 42 |
| policylm | native__e5__balanced4__short | 89.65% | 89.30% | 115 | 44 |
| policylm | native__qwen06__nearest4__short | 91.21% | 91.03% | 84 | 51 |
| policylm | native__qwen4__nearest4__short | 90.17% | 89.94% | 97 | 54 |
| policylm | native__bm25__nearest4__short | 88.35% | 87.90% | 136 | 43 |
| policylm | native__qwen06__nearest2__short | 89.52% | 89.20% | 113 | 48 |
| policylm | native__qwen06__mmr4__short | 91.41% | 91.21% | 85 | 47 |
| policylm | native__qwen06__rerank2__short | 89.84% | 89.54% | 109 | 47 |
| policylm | native__qwen06__rerank4__short | 91.15% | 90.96% | 85 | 51 |
| policylm | native__qwen06__contrast4__short | 92.06% | 91.94% | 71 | 51 |
| policylm | native__qwen06__gated2__short | 90.36% | 90.09% | 102 | 46 |
| policylm | native__e5__fixed0__short | 90.30% | 90.06% | 98 | 51 |
| policylm | native__e5__fixed1__short | 92.32% | 92.35% | 51 | 67 |
| policylm | native__e5__fixed2__short | 90.56% | 90.53% | 71 | 74 |
| policylm | native__qwen06__nearest2__expanded | 88.93% | 88.57% | 122 | 48 |
| shieldstral | policy_only | 98.57% | 98.63% | 3 | 19 |
| shieldstral | original__e5__nearest4__short | 96.61% | 96.52% | 36 | 16 |
| shieldstral | original__e5__balanced4__short | 97.46% | 97.42% | 23 | 16 |
| shieldstral | native__e5__nearest4__short | 96.29% | 96.24% | 32 | 25 |
| shieldstral | native__e5__balanced4__short | 96.35% | 96.41% | 20 | 36 |
| shieldstral | original__qwen06__nearest4__short | 96.48% | 96.32% | 44 | 10 |
| shieldstral | original__qwen4__nearest4__short | 96.22% | 96.05% | 47 | 11 |
| shieldstral | original__bm25__nearest4__short | 96.81% | 96.84% | 19 | 30 |
| shieldstral | original__bm25__nearest2__short | 97.01% | 97.04% | 17 | 29 |
| shieldstral | original__bm25__mmr4__short | 96.68% | 96.71% | 20 | 31 |
| shieldstral | original__bm25__rerank2__short | 96.74% | 96.75% | 23 | 27 |
| shieldstral | original__bm25__rerank4__short | 95.96% | 95.84% | 43 | 19 |
| shieldstral | original__bm25__contrast4__short | 97.20% | 97.17% | 24 | 19 |
| shieldstral | original__bm25__gated2__short | 96.81% | 96.81% | 23 | 26 |
| shieldstral | original__e5__fixed0__short | 97.79% | 97.88% | 5 | 29 |
| shieldstral | original__e5__fixed1__short | 97.59% | 97.65% | 10 | 27 |
| shieldstral | original__e5__fixed2__short | 98.05% | 98.09% | 9 | 21 |
| shieldstral | original__bm25__nearest2__expanded | 97.33% | 97.33% | 19 | 22 |
| kev | policy_only | 87.96% | 87.82% | 103 | 82 |
| kev | original__e5__nearest4__short | 89.32% | 88.87% | 130 | 34 |
| kev | original__e5__balanced4__short | 89.06% | 88.63% | 129 | 39 |
| kev | native__e5__nearest4__short | 88.74% | 88.17% | 147 | 26 |
| kev | native__e5__balanced4__short | 87.63% | 87.08% | 153 | 37 |
| kev | original__qwen06__nearest4__short | 89.06% | 88.58% | 135 | 33 |
| kev | original__qwen4__nearest4__short | 88.54% | 88.01% | 145 | 31 |
| kev | original__bm25__nearest4__short | 88.09% | 87.62% | 140 | 43 |
| kev | original__e5__nearest2__short | 88.61% | 88.11% | 140 | 35 |
| kev | original__e5__mmr4__short | 89.65% | 89.23% | 123 | 36 |
| kev | original__e5__rerank2__short | 87.50% | 86.97% | 152 | 40 |
| kev | original__e5__rerank4__short | 88.80% | 88.32% | 137 | 35 |
| kev | original__e5__contrast4__short | 89.45% | 89.07% | 121 | 41 |
| kev | original__e5__gated2__short | 87.37% | 86.87% | 149 | 45 |
| kev | original__e5__fixed0__short | 88.09% | 87.82% | 117 | 66 |
| kev | original__e5__fixed1__short | 85.87% | 85.27% | 172 | 45 |
| kev | original__e5__fixed2__short | 86.39% | 85.84% | 163 | 46 |
| kev | original__e5__nearest2__expanded | 87.57% | 87.02% | 153 | 38 |
| jev | policy_only | 91.67% | 91.57% | 71 | 57 |
| jev | original__e5__nearest4__short | 93.75% | 93.59% | 64 | 32 |
| jev | original__e5__balanced4__short | 93.88% | 93.71% | 64 | 30 |
| jev | native__e5__nearest4__short | 93.75% | 93.57% | 66 | 30 |
| jev | native__e5__balanced4__short | 93.95% | 93.77% | 64 | 29 |
| jev | native__qwen06__nearest4__short | 93.49% | 93.33% | 66 | 34 |
| jev | native__qwen4__nearest4__short | 93.42% | 93.23% | 70 | 31 |
| jev | native__bm25__nearest4__short | 93.16% | 93.03% | 65 | 40 |
| jev | native__e5__nearest2__short | 93.03% | 92.81% | 76 | 31 |
| jev | native__e5__mmr4__short | 93.75% | 93.55% | 68 | 28 |
| jev | native__e5__rerank2__short | 93.36% | 93.12% | 76 | 26 |
| jev | native__e5__rerank4__short | 93.88% | 93.68% | 68 | 26 |
| jev | native__e5__contrast4__short | 94.01% | 93.81% | 67 | 25 |
| jev | native__e5__gated2__short | 93.16% | 92.93% | 76 | 29 |
| jev | native__e5__fixed0__short | 91.47% | 91.49% | 59 | 72 |
| jev | native__e5__fixed1__short | 91.60% | 91.52% | 70 | 59 |
| jev | native__e5__fixed2__short | 91.60% | 91.50% | 72 | 57 |
| jev | native__e5__nearest2__expanded | 93.03% | 92.83% | 74 | 33 |
