# L4 serving: frozen evidence

This bundle records a bounded comparison of vLLM and SGLang for Qwen3.5 4B,
an exploratory long-input control, and a Shieldstral 3B scoring-interface check.
Start with the [plain-language findings](../../docs/cloud-serving/README.md),
[operating tables](../../docs/cloud-serving/RESULTS.md) and
[deployment guide](../../docs/cloud-serving/DEPLOYMENT.md).

The hardware was one NVIDIA L4 rented through GPU.ai. AWS G6 and Google Cloud
G2 offer this GPU, but no AWS/GCP resources were accessed. This does not reproduce
their VM configuration, networking, pricing or service availability.

## What is included

| Location | Contents |
|---|---|
| `registration.json`, `input-freeze.json`, `input-manifest.json`, `policy.json` | Primary contract, fixed policy, hashes and lengths for 64 fitting prompts and the synthetic length workloads |
| `vllm/`, `sglang/` | Fitting candidates, selected settings, consistency checks and 60 primary timed passes |
| `sglang-initial-failed/`, `runtime-amendment.json` | Unsupported text-only flag attempts and the recorded repair |
| `long-input-control/`, `long-control-registration.json` | Eight exploratory passes using the unselected 8,192-token chunk, specified after seeing the primary curves |
| `shieldstral-initial/` | First specialist canary: vLLM passed; SGLang rejected the text-only flag |
| `shieldstral-canary/` | Default-wrapper retry: vLLM passed; SGLang encountered a native-format tensor name while loading |
| `shieldstral-hf-canary/` | Both engines passed after selecting only the pinned Hugging Face files; file hashes, input identities, label log probabilities and scores are retained |
| `runtime/` | Exact accepted launch commands, dependency freezes, setup logs, startup times, hardware and cgroup limits; failed-start logs are also retained |
| `source/` | Executed initial/revised harnesses, setup and controller scripts, HF-file preparation and analysis tools |
| `results.json` | Recomputed primary curves, secondary control and cross-engine/output comparisons |
| `deployment.json`, `billing.json`, `cleanup.json` | Sanitized setup notes, provider usage reconciliation and resource cleanup |
| `SHA256SUMS.json` | Hash manifest for every other file in this bundle |

Private fitting text, serialized token sequences, credentials, connection details
and model weights are excluded. Input row IDs, lengths and hashes support
restoration. Policies reuse previously published training-derived policy text.
See the [reproduction guide](../../docs/cloud-serving/REPRODUCE.md) for input
restoration, runtime commands and score semantics.

The initial primary source hash is in `registration.json`; the revised source
hash is in `runtime-amendment.json`. The initial Shieldstral source precedes
the SGLang top-20 scoring amendment; the final source includes it. The HF-only
registration identifies both its scoring code and file-preparation script.
Dependency/helper code is resolved from the repository; the source map identifies
the preceding implementation commit. The runtime logs preserve the actual
execution order. Shell controllers are provenance snapshots with paths and
completion markers specific to the disposable experiment machine.

## Recompute without GPU or API calls

From the repository root, with NumPy and httpx installed:

```bash
python3 tools/verify_cloud_serving.py --root published_runs/2026-11-01-cloud-serving
```

The check verifies the file manifest, registered source hashes, input identities,
fitting choices, per-request classification contracts, all saved timing metrics,
Shieldstral score normalization, cost and cleanup. It verifies **68 timed passes
and 4,352 valid requests**; it does not independently rerun GPU inference.

To regenerate the human-readable tables:

```bash
python3 tools/write_cloud_serving_tables.py \
  --root published_runs/2026-11-01-cloud-serving \
  --out docs/cloud-serving/RESULTS.md
```

## How to interpret this evidence

The primary input is neutral synthetic text of controlled length, not labeled
WildGuard test content. Both engines receive identical token IDs and return
free A/B classifications. Valid means parseable, not correct. The natural fitting
canary found one label disagreement across engines and one serial/batch change
within each selected engine. Shieldstral's final canary had no label changes.
Neither check establishes equal full-benchmark accuracy.

The two engines use different dependency stacks; SGLang's Qwen wrapper also
retains unused vision weights. Small, warm, closed-loop HTTP measurements on
one machine cannot isolate scheduler code or establish a universal engine winner.
The two repeats average per-pass percentiles rather than estimating production
tail-latency guarantees. Prefix/radix caches are disabled. The 8,192-token control
remains exploratory and does not replace the original fitting selections.

Projected GPU dollars per million assume sustained measured utilization at
$0.59/hour. Actual rental cost includes setup, compilation, failed attempts and
collection. This is not an AWS/GCP price estimate, an L4-versus-L40S hardware
comparison, or an addition to the quality leaderboard.

## Actual cost and cleanup

The rental cost **$0.62** for 3,765 billed GPU-seconds. Cumulative accounted
project spending is **$19.36001787256**, within the $20 authorization and the
study's $1.22 ceiling. The instance had a two-hour automatic termination limit
and was explicitly terminated early. Temporary local/provider SSH keys were
removed, and the provider listed no remaining active instances. No paid inference
API, RunPod, AWS or GCP resource was used.

Earlier studies and bills remain unchanged. The paper, articles and pinned skill
release are separate snapshots; this archive supplies evidence for deliberate
future updates.
