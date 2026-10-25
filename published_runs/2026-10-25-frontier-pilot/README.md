# Frontier API pilot — fitting data only

**Completed:** 32 shared WildGuardTrain fitting prompts × four models × two reasoning conditions = 256 registered observations. One original DeepSeek routing rejection is also retained, for **257 attempted API requests**. This is a compatibility/cost pilot using the unchanged p0 policy, not a tuned-policy experiment or WildGuardTest leaderboard.

Read the [plain-language findings](../../docs/frontier-api/READOUT.md), [registered plan](../../docs/frontier-api/PLAN.md), and [notebook](../../docs/frontier-api/NOTES.md).

WildGuardTrain's supplied labels are model-generated. No human-labeled WildGuardTest examples were evaluated in this pilot.

| Condition | Valid one-letter outputs | Correct fitting labels | Reported charge | Mean latency |
|---|---:|---:|---:|---:|
| Astra low | 32/32 | 31/32 | $0.141960 | 1.824 s |
| Astra high | 32/32 | 31/32 | $0.174960 | 2.424 s |
| Opus low | 30/32 | 29/32 | $0.090000 | 2.104 s |
| Opus high | 30/32 | 29/32 | $0.090620 | 2.782 s |
| DeepSeek off | 32/32 | 32/32 | $0.000173 | 0.826 s |
| DeepSeek high | 31/32 | 30/32 | $0.000676 | 1.470 s |
| Kimi off | 30/32 | 28/32 | $0.018855 | 3.223 s |
| Kimi high | 32/32 | 31/32 | $0.033953 | 4.435 s |

Accuracy counts are descriptive for this small fitting-only sample. Do not rank models from them. Failures count as wrong. Astra/Opus do not support reasoning off; DeepSeek/Kimi off returned no reported reasoning tokens. All predictions use strict free-generated A/B parsing, with no label repair or constrained output. Policy tuning, validation selection, held-out testing, and repetition diagnostics have **not** occurred in this frontier study.

## Cost and failures

Reported generation costs sum to **$0.55119753456**. The account usage increase was **$0.551197476**, matching within $0.000001. Cumulative project spend is **$8.46119753456**, against a $20 cap. Six failure responses lacked itemized cost: one original routing rejection, four content-filter responses, and one rate limit. Their entire request ceilings were initially deducted from the local budget. The account reconciliation shows no additional aggregate charge, so those holds were released. Itemized billing for those failures remains unavailable; see [billing.json](billing.json) and both ledger versions. Per-request rounding makes the final conservative ledger $0.551277.

DeepSeek's direct route was rejected by existing account data-use settings before inference. The same checkpoint was explicitly reassigned to DeepInfra FP8; no account settings were relaxed. This one failed provider attempt was reissued on the newly registered deployment. Four prior successful observations were reused. All subsequent filtered, rate-limited, and invalid classifications remain errors and were **not retried**. Before-reconciliation files and source history preserve the accounting and orchestration amendments.

OpenRouter/provider cache discounts affected actual costs, particularly DeepSeek and Kimi. Scaling the observed pilot average to the registered full matrix gives about **$251.50**, with substantial uncertainty about new policies, example lengths, reasoning, and caching. The original scenario estimates and preregistered request counts remain in [cost-estimate.json](cost-estimate.json). The `with_unknown_ceiling` projection in [analysis.json](analysis.json) shows the conservative pre-reconciliation sensitivity, not an additional actual charge.

## Reproduce without API calls

From this directory, use the archived source and public prompt-free records:

```sh
PYTHONPATH=source python3 -m evals.frontier_api.pilot_report \
  --registry source/evals/frontier_api/registry.json \
  --runs runs --estimate cost-estimate.json \
  --out /tmp/frontier-pilot-reproduced.json
```

The resulting JSON must match [analysis.json](analysis.json) exactly. The tool checks unique matched pilot IDs/gold/groups, complete populations, run summaries, and registered deployment identities. `SHA256SUMS` covers the bundle. All runtime source hashes in manifests can be matched to `source/` or `source-history/`; their code commits are recorded in [source-history.json](source-history.json).

`runs/` contains public manifests, original p0 policies, predictions, summaries, and reconciliation sidecars. `source/` contains the current study tools and their dependencies. `source-history/` preserves earlier pilot runtime versions. Catalog/preflight snapshots and the routing amendment document model/provider choices. Gated prompts, raw requests/responses, and account details remain in a separate private archive; no API credentials are included in either run archive.

These are hosted API deployments, not immutable weight snapshots or matched-hardware comparisons. Benchmark training exposure is unknown. The experimenter already knows historical WildGuardTest results. The pilot supports deployment and cost findings; it does not establish superiority over specialized policy models.
