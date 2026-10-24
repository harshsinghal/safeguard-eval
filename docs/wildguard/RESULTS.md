# WildGuard results

All 84 runs are complete, covering pilot, policy search, validation, internal audit, official test and expanded fitting. The [full evidence report](../../published_runs/2026-10-24-wildguard/README.md) contains methods, controls, intervals and artifact links for 158,628 row-level predictions.

On all 1,699 labeled official-test prompts:

| Model | Initial policy | Validation-selected policy |
|---|---:|---:|
| Shieldstral (preselected primary) | 87.93% | 90.82% |
| CoPE | 90.46% | 90.76% |
| GPT-OSS Safeguard-20B | 89.82% | 89.64% |
| PolicyLM-1.7B | 85.05% | 86.82% |
| WildGuard official baseline | 90.35% | — |

Shieldstral improves by 2.88 percentage points over its initial policy, with paired 95% interval [2.00, 3.83]. Its +0.47-point advantage over WildGuard has an interval of [−0.24, 1.24], so superiority is not established. Initial-policy threshold calibration alone reaches 90.11%; the remaining tuned-policy advantage is also uncertain.

All errors remain in the denominator. The study uses a bounded search and sampled fitting/validation/audit populations; it does not claim full-training optimization or general superiority to fine-tuning. All policy candidates, negative results, model exposure limitations and operational failures are retained.

All five models ran on GPU.ai. Provider-reported cost is **$4.30** for this study and **$5.87** including earlier experiments. The GPU is confirmed terminated, temporary SSH keys are removed, and raw traces are preserved in a separate private archive. Runpod was not needed.

See the [lab notebook](NOTES.md), [claim-to-evidence map](CLAIMS.md), [result figure](../../published_runs/2026-10-24-wildguard/figures/policy-tuning.png), and [machine-readable progress](progress.json).
