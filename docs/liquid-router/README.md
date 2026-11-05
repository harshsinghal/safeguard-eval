# Liquid CPU classifier for benchmark families

We trained **Liquid LFM2.5-Encoder-350M** to identify seven pooled safety-benchmark
families from text. The validation-selected fine-tune achieved **89.20%
held-out accuracy and 90.07% macro F1**. A text-only linear
control scored 80.00% accuracy and 80.84% macro F1.
This is a working CPU classification backend and an exploratory routing baseline.
It is not a validated system for deciding which safety checks can be skipped.

[CPU usage and reproduction](RUNNING.md) · [Locally registered plan](PLAN.md) ·
[Protocol](protocol.json) · [Frozen evidence](../../published_runs/2026-11-05-liquid-router/README.md)

## What it predicts

The categories are agent safety, source-code safety, cyber requests, general
request harmfulness, hate speech, prompt injection, and skill safety. Thirteen
benchmark tasks pool into these seven categories. Each source supplies one
benchmark-family target. Other applicable categories remain unannotated.
The model receives only input text; source IDs, benchmark names, gold moderation
decisions and category labels are not appended as features.

A category name identifies a check to consider, not a violation. Benign and
harmful examples both occur in training: 1,803 ALLOW and 1,513 BLOCK records.
Returning `harmful_requests` does not mean the prompt is harmful. The API returns
category scores, candidate routes and a low-confidence fallback flag; its
moderation decision is always null. No guard-model dispatch was performed.

## Held-out CPU quality and speed

All 983 fixed evaluation inputs were preserved and received predictions. Quality
headlines cover 935 inputs from supported families. The 48 custom-policy inputs
have no suitable fitting split and are an explicit unsupported-category diagnostic.

| CPU mode | Accuracy | Macro F1 | Median latency | p95 latency |
|---|---:|---:|---:|---:|
| FP32 | 89.20% | 90.07% | 127.6 ms | 278.7 ms |
| Dynamic INT8 linear layers | 88.45% | 89.03% | 60.0 ms | 144.3 ms |

Measurements used an **Intel(R) Core(TM) Ultra 7 270K Plus**, four Torch threads and batch one.
Warm latency includes tokenization and classification, excludes model loading,
and comes from one serial pass through mixed-length inputs on a desktop, without
system isolation. Cold load was 1.92s for FP32 and
3.41s for INT8. These are single-host measurements,
not a throughput or concurrency benchmark. The installed Torch build supports
CUDA, but the inference model, tensors and quantization all ran on CPU.

INT8 was 2.13 times faster by median latency. It changed
27 top-category predictions across all 983 inputs and reduced supported-case
accuracy by 0.75 percentage points. It is an optional faster
mode; FP32 remains the quality reference. In particular, skill-package family
recognition fell from 98.39% to 88.71%.
Dynamic INT8 applies to linear layers, not every operation or tensor.

Grouped bootstrap 95% accuracy intervals were
86.97%–91.07% for FP32 and
86.27%–90.44% for INT8. These exploratory intervals use
observed source/scenario groups and reused tests. They do not address unknown
pretraining exposure, unmeasured semantic dependencies or deployment shift.

| Reference family | Cases | FP32 family recall | INT8 family recall |
|---|---:|---:|---:|
| agent_safety | 250 | 100.00% | 99.60% |
| code_safety | 62 | 96.77% | 98.39% |
| cyber_safety | 63 | 100.00% | 100.00% |
| harmful_requests | 63 | 95.24% | 93.65% |
| hate_speech | 63 | 100.00% | 100.00% |
| prompt_injection | 310 | 69.35% | 69.35% |
| skill_safety | 124 | 99.19% | 94.35% |

## The injection-family gap matters

| Source task | Cases | FP32 family accuracy | INT8 family accuracy |
|---|---:|---:|---:|
| injection_deepset | 62 | 98.39% | 100.00% |
| injection_xtram | 62 | 83.87% | 85.48% |
| benign_lookalikes | 63 | 25.40% | 25.40% |
| jailbreak_attempts | 62 | 48.39% | 43.55% |
| injection_context | 61 | 91.80% | 93.44% |
| skill_packages | 62 | 98.39% | 88.71% |

The model fitted injection examples from deepset and xTRam; benign lookalikes,
jailbreak attempts and synthetic injection-context cases were held-out sources.
Skill-package cases were also held out from fitting; fitting used skill text.
These diagnostics expose transfer limits that the overall validation score hides.
Of 95 FP32 injection-family errors, 89 were assigned to general harmful-request
checking. Source-family mismatch alone does not establish that a proposed safety
check is inappropriate: harmful requests, jailbreaks and ordinary benign requests
can overlap across benchmarks. It does establish that source membership is an
incomplete routing annotation. Reviewed, overlapping applicability labels are
needed before treating this as a reliable semantic multilabel router.

The validation-selected candidate count was one, because it exceeded 95% overall
reference-family coverage on validation. It reached only 89.20%
on the supported final cases. We preserved that failed transfer rather than
changing the deployed selection after inspecting the test. Low-confidence
fallback occurred on 5.39% of all FP32 cases. Only
33.33% of unsupported custom-policy cases triggered it, showing
that this flag is not a dependable unknown-category detector.

## Fitting and selection

There were **3,316 fitting and 850 validation inputs**, drawn from archived fitting
and validation splits. Original fitting populations were hash-sampled to at most
512 inputs per category. Empty original texts were excluded and recorded.
No original final-test population was repurposed for fitting. Known groups,
normalized exact matches and approximate word-five near-duplicate groups
excluded development records touching the fixed suite or its calibration panel.
All 983 final input hashes match the fixed benchmark. Audit groups are disjoint,
and no exact 256-token model view occurs across fitting, validation and test.
Near-duplicate retrieval is approximate and cannot prove semantic independence.

One seed and learning rate, with up to three epochs, were locally registered
before fitting; the registration is published with these results. Class-balanced
cross-entropy updated the complete encoder and head. The head started from the
fitted frozen-encoder control. The first fine-tuned checkpoint won validation
macro F1, and was frozen before final CPU inference. Later epochs are retained
as negative selection evidence. No final-score replacement was made.

| Candidate | Validation accuracy | Validation macro F1 |
|---|---:|---:|
| frozen  | 95.88% | 95.95% |
| full_finetune 1 | 97.18% | 97.23% |
| full_finetune 2 | 97.18% | 97.17% |
| full_finetune 3 | 96.47% | 96.47% |

Validation selected temperature 2.0, one candidate route, and the predeclared
fallback cutoff of 0.6. Softmax scores estimate a single reference family; they
are not independent probabilities of all applicable risks. The 256-token input
view uses the first 96, middle 64 and final 96 tokens. **41.10% of
final cases were shortened.** This routing view does not establish safety for
omitted text. Original source judgments include human, model-derived and
synthetic labels. The fixed suite itself still has pending reference/policy review.

Raw per-track records retain fixed-seven-label macro calculations; zero-support
labels make these unsuitable as standalone task headlines. Use the per-track
accuracy/coverage columns above. The overall macro F1 covers all seven supported
families. These metrics are distinct from the enterprise moderation suite's
severity-weighted ALLOW/BLOCK/REVIEW score.

## Execution and next development step

The local 5090 run lasted 23.8 minutes, with 19.8% measured operation duty.
Device-sampled peaks were **45C and 171W**. Power samples can miss instantaneous
peaks and include other device activity. Hardware power/clocks were unchanged;
no paid compute was used. The experiment's GPU process exited before CPU
measurements. Local electricity and engineering time are not priced.

Preflight checks caught an incompatible direct encoder weight loader, an empty
fitting prompt, and a synthetic-input hash adapter issue before fitting began.
The final loader rejects missing/mismatched/unexpected weights, the original
pretrained embedding tensors were checked, and a portable checkpoint passed an
offline FP32 round trip plus INT8 smoke inference. Selected encoder weights were
independently confirmed to have changed. All 37 router, artifact and benchmark tests pass.

The usable checkpoint stays in ignored
`work/liquid-router-v0/checkpoints/epoch-1`, including weights, tokenizer, pinned
model code, head and routing settings. Publishable evidence contains no source
text, model weights or credentials. Original studies and the fixed benchmark
remain unchanged. Qwen, Shieldstral runtime sweeps and guard selection were not run.

The next quality step is an independent, reviewed applicability-label layer:
allow several relevant checks per input, include benign domain examples and
unfamiliar categories, and hold out sources. Evaluate actual missed harms and
unnecessary blocks after guard dispatch separately from family attribution.
