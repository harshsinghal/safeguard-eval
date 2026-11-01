# Serving moderation models: frozen evidence

This bundle records a small-budget latency, throughput and GPU-cost study of
seven previously evaluated classifiers. Read the [plain-language results](../../docs/serving/README.md)
and [complete operating profiles](../../docs/serving/RESULTS.md) first.

## What is included

| Directory | Contents |
|---|---|
| `reference/` | Seven original runtime profiles, frozen serving settings, repeated request timings, policies, environment logs and historical output references |
| `optimized/` | Separate Kev/Clef optimized-kernel attempts, fitting consistency gates and any accepted measurements |
| `policy-batching/` | Rejected PolicyLM internal token-budget extension; fitting gates and failures, no final measurements |
| `analysis/` | Recomputed summaries, CSVs, output-agreement audits and cross-runtime comparisons |
| `source/` | The executed source snapshots, dependency base, installed packages/setup records and controller logs |

The original [plan](PLAN.md), [implementation amendments](AMENDMENTS.md), and
[interface notes](COMPATIBILITY.md) preserve changes in scope and compatibility
repairs. Subsequent operational extensions have their own registrations. They
keep model weights, policies and classification cutoffs fixed.

The 96 fitting and 384 measurement prompts are identified by dataset row ID and
SHA-256. Measurement prompt text is not duplicated in this bundle. Policies may
contain previously published fitting examples. The selected Liquid checkpoint
was retained locally; its hash is public, but its 1.4 GB weights are not in Git.
No API credentials or SSH keys are included.

## Recompute and reproduce

Follow [the reproduction guide](../../docs/serving/REPRODUCE.md). Recomputing the
summary tables needs no GPU or paid API calls. A new inference run requires the
registered weights, vendor code, restored inputs, compatible hardware and a
separately controlled compute budget.

Every pass has a small summary JSON and a gzipped per-request trace. Request IDs
and hashes allow pairing across models and settings. The summary's “valid” count
means a parsed binary classification, not a match to a ground-truth label. This
study neither retunes policies nor replaces the accuracy leaderboard.

`complete.json` marks accepted completed measurements for a model. Earlier
failure files are retained for provenance. The invalid WildGuard tokenizer
attempt is under `reference/runtime/wildguard-tokenizer-attempt/`; it is excluded
from the results. An explicit check found different token sequences for all 480
inputs with the newer tokenizer backend. Accepted WildGuard timings use the
pinned slow tokenizer. See the source map for the exact execution sequence.

Three repeated passes of a small finite workload provide pilot estimates. The
client uses HTTP loopback and closed-loop concurrency. The study does not measure
Internet latency, production arrival queues, long documents, many tenants,
multiple simultaneous policy questions, image moderation or ensemble serving.
GPU cost per million assumes sustained measured load on a warm GPU at the
recorded hourly rate; it excludes idle time and the rest of production operations.

## Actual cost and shutdown

The run cost **$1.65**, covering 7,434 billed GPU-seconds at
$0.80/hour. Setup, failed attempts, compilation and collection are included.
Cumulative accounted project spend is **$18.74001787256**. The study stayed within
its $5 ceiling. The GPU was terminated, temporary provider/local SSH keys were
removed, and the provider listed no remaining active instances. RunPod and paid
inference APIs were not used. See [billing](billing.json),
[provider usage](gpu-billing.json) and [termination](termination.json).

The check report and SHA256SUMS file cover the published artifacts. Prior studies
and their bills remain unchanged. The paper, articles and pinned agent skill are
separate snapshots and were not rewritten as part of this serving experiment.
