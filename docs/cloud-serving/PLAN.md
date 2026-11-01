# Serving on a GPU offered by both major clouds

## Question and scope

How does input length change the cost of moderating a request on one NVIDIA L4
(24 GB), and how do vLLM and SGLang compare on the same classification workload?
This follows the seven-model [L40S serving study](../serving/README.md).

Use Qwen3.5 4B as the primary engine comparison. Attempt Shieldstral 3B as a
specialist comparison if both engines preserve its scoring interface and time
permits. This is a bounded serving pilot, not a new accuracy leaderboard or a
search for globally optimal settings. Native PolicyLM, Kev, Clef and Liquid
interfaces are not automatically converted into ordinary text generation.

## Hardware and spending

The [AWS G6](https://aws.amazon.com/ec2/instance-types/g6/) and
[Google Cloud G2](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines)
families offer NVIDIA L4 GPUs with 24 GB. Test an L4 rented through GPU.ai;
do not access AWS or GCP accounts. Matching the GPU does not reproduce cloud VM
CPU, RAM, networking, price, autoscaling or zone availability.

The observed GPU.ai offering is one L4, four CPU cores, 19 GB RAM and a default
100 GB filesystem at $0.59/hour. Reserve up to $0.014/hour for disk conservatively
until the final bill is reconciled. Limit the instance to two hours using the
provider's auto-termination control: a conservative maximum of $1.208, rounded
to a $1.22 study ceiling. Cumulative previously accounted spend is
$18.74001787256; this study must stay within the remaining $1.25998212744 of the
$20 authorization. Shut down early when measurements finish.

## Fixed model and input contract

Reuse the exact Qwen model revision and policy from the preceding serving study.
Pin vLLM 0.32.0 and SGLang 0.5.23, and record their different dependency stacks.
Use BF16, no quantization, one GPU, an 8,192-token total context limit and at most
32 active requests. Render the historical chat template once, using one pinned
tokenizer, and send identical token IDs through each engine's completion API.
Preserve the free A/B decision, thinking disabled, temperature zero and an
eight-token generation cap. No forced-label grammar. Compare resulting labels
on 32 unmodified fitting examples before reporting an engine speed comparison.
Record disagreements; do not silently treat changed outputs as equivalent work.
This pilot requests the primary label only, omitting the auxiliary log-probability
payload used in the preceding L40S study. It is a matched engine comparison on
the L4, not a controlled L4-versus-L40S hardware comparison.

## Length and load

Separate submitted content from the complete input (policy, chat framing and
content). Build deterministic synthetic documents with 64, 256, 1,024 and 4,096
submitted-content tokens. Use distinct documents and report actual full token
counts. These are load inputs without inherited benchmark labels: lengthening or
concatenating content does not preserve a WildGuard ground-truth label. Include a
mixed-length workload with equal counts from the four bins.

Run 64 distinct inputs per length/load condition, two repeats, at concurrency
1, 8 and 32. Closed-loop throughput measures saturation behavior; it does not
model production arrival rates or a latency service-level guarantee. Exclude
startup and warm-up from steady-state latency and report them separately.
Disable prefix/radix caching in the primary comparison to avoid repeated-content
reuse and isolate the cost of processing length. Shared-policy caching and
multi-tenant cache churn remain separate follow-ups; the preceding study already
documents their architecture dependence.

Choose each engine's chunked-prefill budget from 2,048 and 8,192 using only the
same 64 unmodified fitting prompts at concurrency 16. Select the highest valid
throughput with no request errors. This gives equal candidate counts, not equal
internal scheduling or a globally optimized engine. Freeze before length tests.
Cap startup attempts and leave at least ten minutes for export and cleanup.

## Report

Report valid classifications/second, p50 and p95 complete-request latency,
errors, full input lengths, output token counts, label consistency and GPU-only
cost per million at observed utilization. Include environment and exact launch
commands, startup time, memory readings, setup failures and cost/termination
evidence. Small samples make p95 estimates provisional. Do not compare engine
speed if the output contract fails; publish the compatibility result instead.

Policy length, context length and deployment quality are different axes. Keep
policy text fixed here. Later policy-length experiments must use meaningful
short and detailed versions, assess quality separately, and preserve a held-out
set. A long synthetic document is not an evaluation of enterprise governance.

## Specialist compatibility check

Before running the optional Shieldstral work, narrow it to a fitting-only
interface canary: 32 original prompts, serial and at concurrency 16, under each
engine. Use the historical policy, fixed 0.5 threshold and exact model revision.
Both engines generate one token and must return log probabilities for the same
yes/no alternatives. vLLM exposes arbitrary token probabilities through its
completion API; SGLang exposes them through native `/generate`. Normalize the
maximum log probability for each label's registered token variants, exactly as
the earlier adapter did. Do not invent a missing alternative.

Keep the 2,048-token serving budget fixed for this canary. Accept batch
consistency only with zero errors, at most one label change and at most 0.02
absolute score drift. Report cross-engine differences separately. This checks
the specialist scoring interface; it does not produce a Shieldstral throughput
curve or establish equal moderation quality. Its separate registration is
[SHIELD-REGISTRATION.json](SHIELD-REGISTRATION.json), written before execution.

## Compatibility amendment before accepted SGLang inference

Both SGLang chunk candidates failed before model inference because SGLang 0.5.23
restricts its standalone `--language-model-only` flag to other architectures.
Remove that flag for SGLang and use its supported default model wrapper. Keep
the vLLM setting and all input IDs, BF16 precision, labels and tuning rules
unchanged. Preserve the initial failures separately and rerun SGLang fitting.
The SGLang wrapper can load unused vision weights even for these text requests;
record its memory footprint. This is a comparison of deployable runtime bundles,
not an isolated scheduler comparison with guaranteed identical resident tensors.
Retain the initial Shieldstral canary as well and rerun it after the same repair.

The repaired default Shieldstral loader subsequently failed on the Mistral-format
tensor name `layers.0.attention.wk.weight`. Its pinned repository contains both
`consolidated.safetensors` and `model.safetensors`. A final fitting-only canary
uses a local directory of the published Hugging Face-format files, with every
file checksummed and no tensor transformation. Run both engines through the
same scoring check; compare vLLM to its original scores as well. Preserve both
earlier failures. This checks a loading path, not a new throughput claim. See
[the HF-only registration](SHIELD-HF-REGISTRATION.json). Perform file preparation
after the timing controls to avoid competing with measured inference.

## Progress

- [x] Prior study recorded and published; standing update workflow added.
- [x] Common-cloud GPU verified; current provider capacity checked.
- [x] Prepare and validate harness; pin inputs and runtime choices.
- [x] Provision bounded instance; execute supported comparisons.
- [x] Export evidence, terminate resources and reconcile actual cost.
- [x] Record findings, deployment implications and README links for publication.

The completed [readout](README.md) and [evidence bundle](../../published_runs/2026-11-01-cloud-serving/README.md)
record both primary engine curves, the exploratory long-input control and all
three Shieldstral loading attempts. The final HF-only canary passed on both
engines. The rental cost $0.62; termination and temporary-key removal were
confirmed. No full benchmark accuracy evaluation was added.
