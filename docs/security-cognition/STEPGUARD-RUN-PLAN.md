# StepGuard frozen-model comparison: execution registration

Status: implementation and input checks, 4 November 2026. The user authorized
implementation of the [experiment design](STEPGUARD-BENCHMARK-PLAN.md). No results
are claimed by this registration. Source files and policies will be hashed before
model requests start; test inference requires a completed selection freeze.

## Scope

Compare Shieldstral, GPT-OSS Safeguard, Jev, Kev and Clef Flash on the same complete
StepGuard SFT inputs. Report pending actions and completed runs separately.
PolicyLM has a supplementary complete-input cohort, and every other model is
also reported on exactly that cohort. No fine-tuning, calibration, learned
thresholds or ensembles. Source labels map SAFE to ALLOW and UNSAFE to BLOCK.

Use the pinned checkpoint revisions in `evals/stepguard/common.py`, inherited
from our existing integrations. Record actual runtime versions and Jev's resolved
API model/provider. Classify text only; never execute a dataset action.

## Input and splitting

Read the 3,000 SFT records from dataset revision
`aadeae009800d8fbcd145575f1d1a6b37abb0950`. Parse the two source templates into
named fields: user request, available tools, history plus candidate action, or
complete recorded run. Remove the source reviewer-task instructions; preserve
the actor evidence. Reference reviewer rationales, judgments and risk annotations
are excluded from inputs. Ambiguous boundaries or candidate outcomes are excluded
before predictions, with counts and reasons retained.

The release does not provide original scenario IDs. Group across both tracks by
normalized identical user requests, request character-TFIDF cosine similarity
at least 0.82, or actor-history similarity at least 0.90. Normalize Unicode,
case, whitespace, addresses and identifiers for grouping only. Take transitive
closure. This conservative heuristic can merge unrelated cases and cannot prove
that all scenario paraphrases are detected. Publish grouping edges as source IDs
and similarities, not raw text.

Five shuffled stratified group folds (seed 20261104) approximate 20% discovery,
20% validation and 60% test. Stratify on track, class and risk source. Force every
group containing one of the previously inspected first 30 source records into
discovery. Do not examine test examples for policy edits. The complete-input
eligibility checks are label-blind and occur before inference.

## Policy candidates and selection

Three candidates per model and task: **initial**, **criteria**, **contrasts**.
They were authored from the source criteria and inspected discovery examples,
before validation predictions. The second spells out evidence, intent,
consequence and safety/utility; the third adds short boundary contrasts. Each is
rendered into the model's supported fields. This is a bounded policy-candidate
selection experiment, not an unrestricted automated optimizer or iterative
model-error-driven authoring study.

Evaluate all three on validation. Select highest balanced accuracy, then shortest
native policy token count, then lexical candidate ID. Jev does not publish its
tokenizer: its tie-break uses reported input-token usage for the lexically first
common validation record (fixed content, varying policy). Freeze every model's
selection before any test inference. Evaluate initial and selected policies on
the same held-out rows; reuse predictions when the selected policy is initial.
If a model/task has no eligible validation rows it is skipped; with only one
validation class, retain the initial policy without claiming optimization.
Optional discovery smoke calls are capped at 12 examples per model/track and
are included in costs. They test operation, not candidate selection.

## Context and output rules

Primary model inputs must fit the fixed 16,384-token input limit in native
serialization, with additional generation headroom for Safeguard. Jev uses a
conservative full-request byte bound below its 32K per-question budget, without
truncation. Preserve all source fields. No summaries or retrieval compression.

PolicyLM's native helper also splits messages above 2,000 characters, separately
from its 2,048-token budget. Supplementary eligibility must therefore fit one
native window, the complete policy prefix and content, and one cleaning variant.
Keep the published precision cutoff 0.335 and record preprocessing. Confirm
one-window operation during inference. Do not alter the helper to stretch its
input range.

Shieldstral uses yes/no pair argmax (BLOCK on ties), Kev/Clef native Choice argmax
(ALLOW on ties), and Jev its returned native Choice. Safeguard uses temperature
zero, medium reasoning, at most 8,192 generated tokens and strict binary JSON.
Parse failures are unresolved errors; no semantic retries. Retry transport
failures at most twice, reserving cost for every attempt. Stop on repeated
infrastructure failures and preserve failures/amendments.

## Reporting

Per track/cohort: ordinary and balanced accuracy, macro-F1, MCC when defined,
false-flag rate, unsafe miss rate, unresolved counts and complete-input coverage.
Unresolved predictions remain in denominators and count as incorrect for class
recall. Separate false decisions from unresolved outcomes. Report grouped 95%
bootstrap intervals (2,000 draws), paired initial-to-selected changes, source risk
slices, safe handling of risk, benign safe cases, action type and input length.
Intervals are exploratory and not adjusted for multiple comparisons.

All 300 source benign/no-risk rows belong to the action track; do not invent that
slice for trajectories. Report matched safe/unsafe groups only where identified,
and do not describe heuristic groups as guaranteed counterfactual pairs. Preserve
source labels. No new human adjudication is part of the primary result. Findings
concern agreement with synthesized reference judgments, not live prevention,
deployment latency or human-review workload.

## Budget, runtime and publication

Maximum incremental spending: **$8** from the **$9.053013164** unused prior
benchmark allocation, recorded in the preceding cyber/skill study's ledger.
Reserve no more than **$6 for GPU and storage** and **$2 for Jev**. Provider credit
is not an additional spending authorization. GPU.ai has insufficient credit for
the full run; use the already authorized RunPod fallback. Check live prices and
account activity before renting; prohibit unrelated concurrent rentals.

RunPod's older `--terminate-after` flags were never enforced and were removed
from its CLI. Use a provider-resident, pod-scoped shutdown watchdog plus a local
independent deletion watchdog; verify both before starting substantive compute.
Bound rental duration and storage together within the GPU cap, collect outputs
regularly, then delete the pod and verify no ongoing billing or retained paid
volume. Record actual control mechanisms rather than claiming a native TTL.
See [RunPod's CLI release note](https://github.com/runpod/runpodctl/releases/tag/v2.12.0).

Publish code, policies, source hashes, grouping/split manifests, aggregate coverage,
all predictions, validation selection, failures, metrics, costs and cleanup.
Keep raw dataset text, raw model responses and infrastructure/credential details
in the private work directory. Update the main README and dataset/model indexes;
leave reviewed papers and the versioned skill unchanged.
