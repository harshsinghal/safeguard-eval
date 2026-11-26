# Learning which guard is likely to succeed

Implemented and evaluated locally; published to the repository on 25 November 2026 with prompt-free evidence.

The actual two-stage system scored **75.89% (85/112)** on the
reserved competence test, versus **75.89%** for Clef alone. Validation did not support any challenger; the frozen routing rule uses Clef for every input.
These are exploratory reference-label results, not independently adjudicated
enterprise deployment accuracy.

| System | Reserved test | Exposed pilot diagnostic |
|---|---:|---:|
| Clef alone | 75.89% | 75.00% |
| Original category router | 79.46% | 72.32% |
| Conservative policy-category control | 75.89% | 75.00% |
| Liquid competence router | 75.89% | 75.00% |

The reserved panel contains 112 binary cases across ten tasks, selected by
category/label strata from the archived Liquid validation pool. Those texts and
family labels were exposed in earlier category-classifier validation; this is a
new competence-routing holdout, not a wholly unseen benchmark. The original
112-case pilot was already inspected and is only a diagnostic. Neither panel
was used to select this study's final routing configuration. Official enterprise
profiles are withheld for the reserved panel because four suite tasks are absent.
The available-task macro recall and per-task/class errors remain in the evidence.

## Model and selection

A pinned pretrained Liquid LFM2.5 Encoder 350M remains frozen on CPU. Four
independent L2 logistic heads learn whether PolicyLM, Shieldstral, Kev and Clef
return the reference decision on the same prompt and policy. Multiple guards can
be correct. Technical failures are masked in semantic fitting and count wrong in
system evaluation. There were 640 training cases (including 192 reused, exact-
configuration calibration cases), 112 validation cases and 112 test cases. Known
source/near-duplicate audit groups and identical bounded views do not cross these
splits. The source benchmark's 983 evaluation cases are protected from fitting.
The original calibration cases are intentionally development data in this study;
see the recorded protocol clarification.

Features comprise a bounded prompt view (256 tokens), a separately bounded
semantic policy view (192), the allowed decision contract and ten structure/
length features. Source names, benchmark IDs, reference labels and guard outputs
are excluded from model features. The selected guard always receives full text.
Policies are trusted application configuration. Editing policy semantics or the
allowed decisions uses the default until supported by validation.

C=0.01 was selected by validation binary log loss. The frozen
switch margin is 1.01; each challenger requires
at least eight switched validation cases and a positive 90% group-bootstrap
lower bound of paired improvement. The combined route must also clear that gate.
This is a conservative exploratory selection heuristic, not a guarantee after
multiple candidate comparisons. All candidates and negative results are retained.
Only ten fitting examples are REVIEW; neither ternary policy has enough separate
validation support to switch away from Clef. Native guard weights, policy text,
thresholds, BF16 precision and adapters were held fixed.

## System verification and resources

Actual HTTP requests attempted a guard on 100.00%
of test cases, with 100.00% successful guard
coverage. Actual decisions differed from the matching direct guard controls on
0 cases. Router/primary-backend failures fall
back to Clef; unresolved errors remain failed REVIEW, never successful ALLOW.
CPU inference is FP32 with four threads; the saved encoder reproduced its features
exactly on an offline reload check. Dynamic INT8 was not part of this study.

Actual request latency: median 845.8ms,
p95 2043.4ms, p99 3197.9ms.
This includes CPU routing, native inference, deliberate cooldown, HTTP and cold
loads when needed. Requests were grouped by selected guard, so this does not
measure simultaneous model residency or natural-traffic switching latency.

Sampled device peak: **56C** and
**358.12W**; mean sampled power across collection
and actual-evaluation windows was **121.22W**.
The software 20% operation duty and cooldown checks limit sustained use and do
not cap instantaneous power. Brief high-power samples are preserved. Device
samples include other applications. No clocks or power limits were changed and
no paid compute was used. All study guard workers and both study gateways were
stopped; the earlier pilot's CPU service was left untouched.

[Plan](PLAN.md) · [Run locally](RUNNING.md) ·
[Local prompt-free evidence](../../local_runs/competence-router-v0/manifest.json)

Recompute and check the evidence without prompts, weights or a GPU:

```bash
python -B tools/report_competence_router.py verify --bundle local_runs/competence-router-v0
```
