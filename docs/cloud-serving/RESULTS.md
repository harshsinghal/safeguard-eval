# L4 serving: all operating points

Qwen3.5 4B, BF16, one NVIDIA L4, fixed policy and identical input token IDs.
Prefix/radix caches are disabled. These are neutral synthetic load documents,
not a new moderation-accuracy evaluation. Each point averages two 64-request
passes. The latency columns average the per-pass percentiles; they are not
pooled percentiles or confidence intervals. GPU rental projections assume
sustained measured utilization at $0.59/hour and are not AWS/GCP prices.

Submitted-content bins of 64, 256, 1,024 and 4,096 tokens produce full inputs
of 466, 658, 1,426 and 4,498 tokens. The mixed group contains 16 from each bin.

| Engine | Content tokens | In flight | Valid/s | Median ms | p95 ms | GPU $/million | Errors / requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| vllm | 64 | 1 | 6.30 | 158.9 | 162.2 | 26.04 | 0 / 128 |
| vllm | 64 | 8 | 11.68 | 684.1 | 690.0 | 14.03 | 0 / 128 |
| vllm | 64 | 32 | 12.91 | 2334.7 | 2677.8 | 12.69 | 0 / 128 |
| vllm | 256 | 1 | 5.11 | 195.6 | 198.6 | 32.05 | 0 / 128 |
| vllm | 256 | 8 | 8.83 | 900.9 | 921.5 | 18.57 | 0 / 128 |
| vllm | 256 | 32 | 9.24 | 3320.2 | 3659.5 | 17.73 | 0 / 128 |
| vllm | 1024 | 1 | 3.20 | 312.6 | 316.3 | 51.27 | 0 / 128 |
| vllm | 1024 | 8 | 4.31 | 1984.6 | 1994.8 | 38.05 | 0 / 128 |
| vllm | 1024 | 32 | 4.31 | 7288.2 | 7625.6 | 38.05 | 0 / 128 |
| vllm | 4096 | 1 | 1.21 | 828.7 | 832.7 | 135.75 | 0 / 128 |
| vllm | 4096 | 8 | 1.34 | 6079.1 | 6094.6 | 121.98 | 0 / 128 |
| vllm | 4096 | 32 | 1.34 | 23691.6 | 24047.0 | 122.14 | 0 / 128 |
| vllm | mixed | 1 | 2.66 | 255.4 | 833.9 | 61.67 | 0 / 128 |
| vllm | mixed | 8 | 3.41 | 2240.0 | 3354.6 | 48.05 | 0 / 128 |
| vllm | mixed | 32 | 3.42 | 7930.9 | 10127.0 | 47.90 | 0 / 128 |
| sglang | 64 | 1 | 6.37 | 156.9 | 159.5 | 25.74 | 0 / 128 |
| sglang | 64 | 8 | 11.97 | 667.6 | 676.2 | 13.69 | 0 / 128 |
| sglang | 64 | 32 | 12.58 | 2422.0 | 2661.3 | 13.06 | 0 / 128 |
| sglang | 256 | 1 | 5.13 | 194.7 | 197.8 | 31.92 | 0 / 128 |
| sglang | 256 | 8 | 8.80 | 908.9 | 916.6 | 18.62 | 0 / 128 |
| sglang | 256 | 32 | 9.42 | 3383.4 | 3404.9 | 17.41 | 0 / 128 |
| sglang | 1024 | 1 | 3.22 | 311.0 | 314.1 | 50.97 | 0 / 128 |
| sglang | 1024 | 8 | 4.27 | 1873.4 | 1881.8 | 38.41 | 0 / 128 |
| sglang | 1024 | 32 | 4.40 | 7253.1 | 7273.4 | 37.24 | 0 / 128 |
| sglang | 4096 | 1 | 1.23 | 815.3 | 819.6 | 133.71 | 0 / 128 |
| sglang | 4096 | 8 | 1.36 | 5886.2 | 5895.8 | 120.60 | 0 / 128 |
| sglang | 4096 | 32 | 1.37 | 23295.0 | 23328.2 | 119.41 | 0 / 128 |
| sglang | mixed | 1 | 2.70 | 255.4 | 817.2 | 60.80 | 0 / 128 |
| sglang | mixed | 8 | 3.41 | 2415.6 | 3501.2 | 48.04 | 0 / 128 |
| sglang | mixed | 32 | 3.51 | 9102.1 | 9898.6 | 46.71 | 0 / 128 |

## Fitting and output checks

- vllm: complete; selected chunk budget: 2048 tokens.
- sglang: complete; selected chunk budget: 2048 tokens.

The two selected engines differed on 1 of 32 fitting labels, with 0 errors.
This small canary is a consistency check, not proof of unchanged benchmark accuracy.

## Exploratory long-input control

The unselected 8,192-token chunk was measured after the primary curves.
It does not replace either engine's original selection. All inputs have
4,096 content tokens (4,498 full tokens). See [the control plan](LONG-INPUT-CONTROL.md).

| Engine | In flight | Chunk | Valid/s | Median ms | p95 ms | Label changes vs primary |
|---|---:|---:|---:|---:|---:|---:|
| vllm | 1 | 8192 | 1.20 | 833.8 | 839.4 | 0 / 128 |
| vllm | 8 | 8192 | 1.30 | 5601.3 | 6934.8 | 0 / 128 |
| sglang | 1 | 8192 | 1.20 | 836.6 | 842.1 | 0 / 128 |
| sglang | 8 | 8192 | 1.29 | 6209.0 | 6231.2 | 0 / 128 |

## Shieldstral HF-only scoring check

Thirty-two fitting prompts, serial and with 16 in flight. These are
score-consistency checks, not capacity or benchmark-accuracy results.

| Engine | Request errors | Batch label changes | Maximum batch score change | Accepted |
|---|---:|---:|---:|---|
| vllm | 0 / 64 | 0 / 32 | 0.00079268 | True |
| sglang | 0 / 64 | 0 / 32 | 0.00127847 | True |

Serial labels differed across engines on 0 / 32 prompts; maximum score difference was 0.00000196.
vLLM's scores before and after selecting the HF-only directory differed by at most 0.00000000.
Both earlier SGLang loading failures remain in the archive. No weights were transformed.

[Readable findings](README.md) · [Deployment implications](DEPLOYMENT.md) · [Reproduction](REPRODUCE.md)
