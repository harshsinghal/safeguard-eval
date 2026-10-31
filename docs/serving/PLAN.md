# Serving moderation models: latency, batching and GPU cost

## Question and scope

What does self-hosting the classifiers already studied cost in time and GPU
capacity? This study measures complete classification requests, not chat token
generation speed. It does not select a new policy or tune classification cutoffs.

Seven pinned systems: Shieldstral 3B, Qwen3.5 4B and WildGuard 7B with vLLM
0.32.0; PolicyLM 1.7B, Kev 4B, Clef-Flash 9B and the selected fine-tuned Liquid
350M encoder with their native PyTorch implementations behind a small HTTP
batching server. Preserve each existing policy, native input format and head.
Jev has no downloadable checkpoint in our study and is outside this self-hosting
comparison. Larger models are outside this small-budget pilot.

The stable vLLM release inspected before launch does not register Clef-Flash,
PolicyLM's bidirectional category-slot model, or our custom Liquid classification
head. Newer upstream source has additional support; that is not evidence of
equivalence to our pinned classifiers. We will not replace their heads or attention
patterns to make them fit a chat server. Native results are explicitly distinct
from vLLM results. Kev uses its pinned publisher implementation.

## Workload and separation

- One NVIDIA L40S, 48 GB nominal, on GPU.ai, currently $0.80/hour; serial model
  execution. Same GPU and client host throughout. HTTP loopback excludes WAN,
  ingress, authentication and multi-tenant overhead.
- 96 unique fitting prompts for serving-configuration selection; 384 distinct
  WildGuardTest prompts for measurements. Hash-based sampling independent of
  labels and length; exact prompt duplicates removed. Prompts stay private.
- Reuse registered policy-transfer recipient selections, decision-model balanced
  selections, and the primary Liquid fine-tuned checkpoint/cutoff. These are
  representative historical systems, not a claim to reproduce every latest
  leaderboard configuration. Full policy and template token lengths differ.
- Warm-up precedes timing. Three repeats per final condition. Concurrency
  1, 8, 32, 64 is a closed-loop load: each client issues another request when its
  previous request finishes. It is not a production arrival-rate SLA test.
- Each timed pass contains unique prompts. Repeat order is randomized. No input
  truncation, policy shortening, quantization or label constraints introduced.

## Bounded tuning

For vLLM compare token scheduling budgets 2,048 and 8,192 at concurrency 32,
with max_num_seqs 64, BF16, maximum context 8,192, memory utilization 0.85,
normal graph/compilation defaults, and prefix caching off. Select the successful
configuration with greatest valid requests/second on tuning inputs. Then measure
the frozen configuration. Also measure shared-prefix caching at concurrency 1
and 32, resetting cache before each pass and warming only with disjoint fitting
prompts. Thus repeated benchmark contents cannot produce full-prompt cache hits.

For native models compare maximum batches 8 and 32 with a 2 ms admission window,
using identical native scoring. Select on tuning throughput, then run the same
concurrency sweep. This is a small serving implementation, not an optimized
commercial scheduler. Report actual batch sizes, tokenization and queue-inclusive
HTTP latency. Native Liquid uses the training study's FP32 weights/BF16 autocast;
other native systems retain their recorded BF16 interfaces.

Record tuning outcomes before final measurement. Failed configurations remain in
the record. Any runtime compatibility changes require an amendment. Compare
batch and concurrency scores/decisions with single-request references; record
numerical differences and errors rather than treating response HTTP 200 as proof
of correctness. Before final timing, a 32-input batch parity gate flags any score
change over 0.02 or more than one decision change for investigation; smaller
differences are still reported. Audit against cached historical predictions where populations
overlap. No measurement-based changes to policies, thresholds or weights.

## Metrics and interpretation

Save individual request elapsed times, IDs/hashes, decisions/scores, input/output
token counts where available, errors, run wall time, software versions, startup
time, GPU telemetry, exact commands and selected configuration. Latency is from
request construction through HTTP response parsing; native queueing and batching
wait are included. Report median and p95, valid classifications/second, error
counts and repeat variability. Single-request latency and loaded latency answer
different questions. Short measurements do not establish p99 service guarantees.

GPU-only dollars/million = hourly price / (3600 × successful requests/second)
× 1,000,000. This assumes sustained load on a warm dedicated GPU. Also show
idle/utilization sensitivity. Include startup/install time in actual experiment
billing, not steady-state throughput. These are system configurations with
different policies, output interfaces and software; not causal architecture
comparisons, equal-quality cost rankings or a claim of globally optimal tuning.

## Budget and completion

Prior cumulative accounted spend: $17.09001787256. The user authorized a few
additional dollars for this experiment; announced study ceiling $5 and resulting
cumulative ceiling $22.09001787256. Reserve at most $4.80 for one six-hour L40S
with provider auto-termination; impose a shorter five-hour controller deadline.
Terminate promptly after artifact collection, verify termination and reconcile
billing. RunPod is available if GPU.ai capacity fails, within the same ceiling.

Completion checklist: registration and code; workload hashes; compatibility
checks; tuning and frozen configurations; repeated measurements; parity audit;
cost/termination evidence; readable results and README link; reproducible raw
timings without publishing benchmark prompt text.
