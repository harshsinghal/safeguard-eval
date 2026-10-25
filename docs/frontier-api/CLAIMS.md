# What the frontier pilot supports

| Claim | Evidence | Limit |
|---|---|---|
| All four selected models can return strict policy labels through the recorded API deployments. | [256 observations and manifests](../../published_runs/2026-10-25-frontier-pilot/analysis.json). | Some calls failed; this is not universal reliability. |
| API filters and service behavior affect the classifier's measured performance. | Four content-filter responses, one rate limit, two invalid final answers, plus the initial routing rejection retained in the bundle. | Do not attribute every failure to the underlying model weights. |
| Higher requested reasoning increased reported reasoning use and average latency in this pilot. | Per-condition token and timing records in `analysis.json`. | Low is not off; provider implementations differ; sequential pilot timing is not a hardware benchmark. |
| More reasoning did not uniformly improve the observed fitting outcomes. | Identical Astra/Opus outcomes; different DeepSeek/Kimi outcomes on the same 32 fitting IDs. | Small sample, model-generated training labels, service failures; no significance or generalization claim. |
| The pilot cost about $0.55 and kept cumulative spend below $20. | [Reconciled billing](../../published_runs/2026-10-25-frontier-pilot/billing.json) and append-only ledger history. | Six failures lacked itemized costs; the account aggregate matched reported charges within $0.000001. |
| Full-study API costs remain outside the current budget at the observed pilot mean. | Registered request counts and approximately $251.50 projection. | A planning scenario, not a quote or measured full-study bill. |

Do not claim that a frontier model won WildGuardTest, that its policy was optimized, or that it beat the historical specialist/Qwen systems: none of those comparisons has run. Do not turn 32/32 fitting matches into a claim of perfect moderation. Preserve the distinction between a valid output, a correct supplied label, and protection of a downstream application.

A useful article angle is **“What a classification API must do before accuracy matters.”** Explain the one-letter contract, filters, reasoning controls, accounting, and why the full experiment needs frozen policy selection and human-labeled held-out evaluation. The [plain-language readout](READOUT.md) is a starting draft; a research-paper section should retain the deployment amendments and exploratory limitations.
