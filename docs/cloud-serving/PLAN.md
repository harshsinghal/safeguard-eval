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

## Progress

- [x] Prior study recorded and published; standing update workflow added.
- [x] Common-cloud GPU verified; current provider capacity checked.
- [ ] Prepare and validate harness; pin inputs and runtime choices.
- [ ] Provision bounded instance; execute supported comparisons.
- [ ] Export evidence, terminate resources and reconcile actual cost.
- [ ] Publish findings, deployment implications and README links.
