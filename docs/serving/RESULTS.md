# All measured serving profiles

One L40S at $0.80/hour. Each row pools three passes of 384 requests. “Valid” means a parsed classification, not a correct label. Cost is a sustained-load GPU-only projection. The rates include each finite pass’s ramp-up and drain.

## Reference runtimes

### PolicyLM 1.7B

Fitting-selected setting: **32 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 34.7 | 42.5 | 27.90 | 27.74–28.11 | $7.96 | 0 |
| Off / native | 8 | 279.0 | 338.6 | 30.41 | 29.87–30.88 | $7.31 | 0 |
| Off / native | 32 | 1054.6 | 1127.4 | 30.95 | 30.65–31.30 | $7.18 | 0 |
| Off / native | 64 | 2039.0 | 2263.5 | 30.79 | 30.23–31.41 | $7.22 | 0 |

### Shieldstral 3B

Fitting-selected setting: **8192 scheduled tokens per iteration**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 37.4 | 45.0 | 26.00 | 25.82–26.32 | $8.55 | 0 |
| Off / native | 8 | 224.1 | 246.8 | 35.53 | 34.47–36.47 | $6.25 | 0 |
| Off / native | 32 | 853.2 | 1134.7 | 35.93 | 35.41–36.48 | $6.19 | 0 |
| Off / native | 64 | 1726.3 | 2010.4 | 35.78 | 35.29–36.23 | $6.21 | 0 |
| On | 1 | 18.8 | 23.2 | 51.94 | 51.82–52.07 | $4.28 | 0 |
| On | 8 | 48.6 | 67.5 | 157.77 | 154.30–161.18 | $1.41 | 0 |
| On | 32 | 131.5 | 171.3 | 236.96 | 234.57–238.53 | $0.94 | 0 |
| On | 64 | 227.9 | 320.2 | 257.37 | 255.41–258.81 | $0.86 | 0 |

### Qwen3.5 4B

Fitting-selected setting: **2048 scheduled tokens per iteration**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 63.1 | 67.8 | 15.67 | 15.34–15.93 | $14.19 | 0 |
| Off / native | 8 | 201.0 | 228.0 | 39.43 | 39.30–39.58 | $5.64 | 0 |
| Off / native | 32 | 769.2 | 777.2 | 42.62 | 42.54–42.77 | $5.21 | 0 |
| Off / native | 64 | 1455.2 | 1550.9 | 42.55 | 42.42–42.71 | $5.22 | 0 |
| On | 1 | 65.1 | 100.9 | 13.46 | 13.25–13.58 | $16.51 | 0 |
| On | 8 | 199.3 | 260.8 | 38.21 | 37.92–38.62 | $5.82 | 0 |
| On | 32 | 736.9 | 865.5 | 42.31 | 42.09–42.44 | $5.25 | 0 |
| On | 64 | 1483.4 | 1611.0 | 42.22 | 41.78–42.50 | $5.26 | 0 |

### WildGuard 7B

Fitting-selected setting: **2048 scheduled tokens per iteration**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 506.4 | 523.0 | 1.96 | 1.96–1.96 | $113.22 | 0 |
| Off / native | 8 | 642.4 | 694.8 | 12.38 | 12.36–12.41 | $17.94 | 0 |
| Off / native | 32 | 1039.4 | 1170.2 | 30.48 | 30.43–30.51 | $7.29 | 0 |
| Off / native | 64 | 1553.1 | 1902.5 | 40.23 | 40.18–40.26 | $5.52 | 0 |
| On | 1 | 504.3 | 516.9 | 1.97 | 1.97–1.97 | $112.73 | 0 |
| On | 8 | 596.4 | 645.6 | 13.39 | 13.28–13.51 | $16.59 | 0 |
| On | 32 | 874.4 | 967.3 | 36.29 | 36.17–36.37 | $6.12 | 0 |
| On | 64 | 1216.5 | 1373.8 | 51.49 | 51.30–51.66 | $4.32 | 0 |

### Kev 4B

Fitting-selected setting: **8 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 61.2 | 74.2 | 16.13 | 15.05–16.94 | $13.78 | 0 |
| Off / native | 8 | 241.7 | 411.0 | 31.77 | 31.03–32.85 | $6.99 | 0 |
| Off / native | 32 | 1078.8 | 1433.2 | 29.00 | 28.71–29.54 | $7.66 | 0 |
| Off / native | 64 | 2103.4 | 2481.2 | 28.96 | 28.63–29.29 | $7.67 | 0 |

### Clef-Flash 9B

Fitting-selected setting: **8 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 177.1 | 202.9 | 5.57 | 5.35–5.76 | $39.87 | 0 |
| Off / native | 8 | 1045.4 | 1506.4 | 7.77 | 7.66–7.98 | $28.59 | 0 |
| Off / native | 32 | 4468.2 | 5016.9 | 7.10 | 7.07–7.11 | $31.31 | 0 |
| Off / native | 64 | 8865.2 | 9408.3 | 7.10 | 7.07–7.13 | $31.30 | 0 |

### Fine-tuned Liquid encoder 350M

Fitting-selected setting: **8 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 14.5 | 16.4 | 68.47 | 66.74–71.00 | $3.25 | 0 |
| Off / native | 8 | 31.0 | 40.7 | 262.96 | 238.80–280.23 | $0.85 | 0 |
| Off / native | 32 | 85.6 | 103.1 | 358.38 | 354.93–363.17 | $0.62 | 0 |
| Off / native | 64 | 172.2 | 344.3 | 329.80 | 300.71–348.62 | $0.67 | 0 |

## Decision-model kernel extension

### Kev 4B

Fitting-selected setting: **8 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 58.6 | 67.7 | 16.75 | 16.65–16.83 | $13.27 | 0 |
| Off / native | 8 | 147.9 | 221.8 | 54.08 | 53.24–55.64 | $4.11 | 0 |
| Off / native | 32 | 506.0 | 638.2 | 61.15 | 60.55–61.62 | $3.63 | 0 |
| Off / native | 64 | 1013.1 | 1148.1 | 60.71 | 60.29–61.54 | $3.66 | 0 |

### Clef-Flash 9B

Fitting-selected setting: **8 maximum outer batch rows**.

| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Off / native | 1 | 73.2 | 95.2 | 12.56 | 12.49–12.62 | $17.69 | 0 |
| Off / native | 8 | 708.9 | 960.2 | 10.65 | 8.98–11.79 | $20.86 | 0 |
| Off / native | 32 | 2935.4 | 3214.3 | 10.82 | 10.71–10.89 | $20.54 | 0 |
| Off / native | 64 | 5793.3 | 6157.7 | 10.81 | 10.76–10.91 | $20.56 | 0 |

## PolicyLM internal token-budget extension

No configuration was accepted, and no measurement pass was run. At maximum batch 8, the 32,768-token budget produced 10.89 requests/s on the 96 fitting prompts, below the original profile. Its 32-input batching check changed 0 labels but shifted a score by 0.02951, exceeding the preregistered 0.02 limit. Maximum batch 32 ran out of GPU memory during fitting-only warm-up. The main comparison therefore retains PolicyLM’s original 1,024-token budget. These are fitting outcomes, not held-out speed results.

## Output agreement

The table reports the largest number of changed decisions in any 384-request pass compared with that runtime’s first single-request pass. Historical differences compare its first single-request pass with the matched archived predictions. Neither is an accuracy score. Qwen probabilities are auxiliary; its generated label determines the decision.

| Runtime | Model | Most label changes in one pass | Largest score change | Historical label changes / 384 |
|---|---|---:|---:|---:|
| reference | Shieldstral 3B | 0 | 0.03121 | 0 |
| reference | Qwen3.5 4B | 3 | 0.06242 | 2 |
| reference | PolicyLM 1.7B | 0 | 0.00000 | 0 |
| reference | Kev 4B | 1 | 0.01415 | 2 |
| reference | Clef-Flash 9B | 2 | 0.01465 | 1 |
| reference | WildGuard 7B | 1 | Not exposed | 1 |
| reference | Fine-tuned Liquid encoder 350M | 1 | 0.03233 | 0 |
| optimized | Kev 4B | 1 | 0.01388 | 1 |
| optimized | Clef-Flash 9B | 2 | 0.01365 | 1 |

Full per-pass and cross-runtime agreement records are in the evidence bundle. A zero on this sample does not prove bitwise equivalence on other inputs. Some numerical differences cross a decision cutoff; evaluate classification quality again before replacing a production runtime.

## Input and output work

| Model | Median full input tokens | p95 full input tokens | Median generated tokens |
|---|---:|---:|---:|
| PolicyLM 1.7B | Not exposed | Not exposed | Native scores |
| Shieldstral 3B | 734 | 997 | 1 |
| Qwen3.5 4B | 433 | 688 | 2 |
| WildGuard 7B | 149.5 | 440 | 24 |
| Kev 4B | 114 | 363 | Native scores |
| Clef-Flash 9B | 621 | 876 | Native scores |
| Fine-tuned Liquid encoder 350M | 33.5 | 293 | Native scores |

These token counts include different policy/template contracts and different tokenizers. Native PolicyLM’s helper does not expose a comparable per-request token count through this interface. GPU memory reservation is not a measurement of the minimum GPU needed.
