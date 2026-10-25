# Qwen comparison lab notebook

## 2026-10-25 UTC — protocol and model selection

The user requested nearby-size general-purpose Qwen instruction models as a comparison with the five policy/WildGuard deployments. Qwen3.5 has 2B, 4B, 9B and 27B dense language models and a 35B-total/3B-active mixture-of-experts model. CoPE is 25.2B total / 3.8B active, so treating it as an ordinary 4B model would be misleading. Safeguard is also a mixture-of-experts model. Both receive separate total-size and active-size comparisons.

The policy document is itself an instruction. We preserve its substantive text and render it in a general-purpose model's system message; model specialization and deployment differ. The original policy files, predictions and study remain immutable. Prior test results are already known to the experimenter, so all new conclusions are exploratory. Reusing the same test enables paired comparisons but does not restore an unseen holdout.

No new paid resources are active at protocol drafting. Existing spend is $5.87, leaving at most $4.12 under the original cap. The planned main deployment disables Qwen thinking explicitly, uses free-generated binary letters, and counts refusals/truncations/invalid output as errors. Its output format and runtime differ from native policy classifiers; these are system comparisons.

## Pre-inference implementation checks

Pinned all five Qwen checkpoint revisions and their full checkpoint parameter counts (2.274B, 4.660B, 9.653B, 27.781B, 35.952B). The advertised language-model sizes exclude some vision-related weights. All 26 local tests pass, including strict classification parsing, rejecting refusals and truncations, separation of policy and submitted text, and rejecting changed frozen sources, policies or populations. Historical WildGuard code and artifacts are unchanged. GPU.ai reports $19.50 credit, no active instances, and an available secure 96 GB RTX PRO 6000 VM at $1.99/hour including disk. Credit availability does not increase the user cap.

## Pilot observations on the first three models

The 2B, 4B and 9B models each returned 256 valid labels, with complete token-score coverage. Initial-policy pilot accuracy is 85.94%, 90.63% and 93.75% respectively. These are fitting-only observations, not evidence of test performance. The 2B model has 30 false blocks and six missed harmful requests; fitting-error inspection shows false blocks on benign fictional records, ordinary advocacy, prevention/privacy discussion and harmless requests with suspicious framing. Misses include protected-work reproduction and harmful output disguised as fiction. No source examples or names will be copied into policies.

The 2B pilot's 65.76-second wall time is dominated by its first requests (around 64 seconds for many first-batch requests); median per-request latency is 0.237 seconds and the final requests take about 0.1 seconds. The 4B and 9B pilots take 8.02 and 9.99 seconds. These startup/batching-dependent observations cannot support a clean latency ranking. All settings remain as registered; no pilot decoding amendment is needed so far.

## Deployment and remaining scope

GPU.ai instance gpu-e4319df3 became ready at 2026-10-25T03:29:48.416494Z at $1.99/hour, with provider cutoff 2026-10-25T05:29:48.416494Z. The secure VM includes its disk; two hours nominally cost $3.98 and keep cumulative spend below $10. Public Qwen checkpoints download without staging any user token. A phase gate starts shared-policy runs only after all five pilots complete without output failures; no pilot accuracy threshold selects or excludes a model.

Qwen's original training exposure to WildGuard is unverified. Nearby parameter counts also leave differences in architecture, model age, training data and decoding. The historical Safeguard deployment used medium reasoning and MXFP4 while this Qwen study uses non-thinking BF16. We will report those conditions and avoid claiming an isolated specialization effect or a controlled speed ranking.

## First model-specific candidates

Qwen 2B's p0/p1/p2 fitting accuracies are 82.91/83.79/86.04%, with validation 84.18/86.72/87.70%. Its p2 still has 82 false blocks and 61 misses. Two fitting-derived drafts distinguish ordinary competition, figurative language, public facts and harmless fiction from practical harmful deliverables; the second tests a shorter evidence-based formulation. Protected-work reproduction, harmful transformations and disguised assistance remain in scope. Ambiguous or contextless source labels are retained without memorized exceptions.

Qwen 4B's p0/p1/p2 fitting accuracies are 90.33/91.80/91.11%, with validation 89.45/91.02/90.43%. Its p1 has 41 false blocks and 43 misses. One draft clarifies requested deliverables and benign history/prevention/creative exceptions; the other tests direct harmful statements and endorsements as well as requests. That second candidate changes a scope boundary, rather than merely polishing wording. Both hypotheses are registered before model-specific inference, and all failures will be retained.

## Larger-model candidate hypotheses

Qwen 9B's p0/p1/p2 fitting accuracy is 92.38/93.16/91.60%, with validation 92.38/93.36/93.75%. Its p1 fitting errors include 26 false blocks and 44 misses. The first tailored draft makes degrading social portrayals and real-person health/financial information explicit; the second tests compact rules that still count requests to validate harmful beliefs. Both preserve benign criticism and require evidence rather than imagined hidden context.

Qwen 27B's p0/p1/p2 fitting accuracy is 92.48/94.04/93.16%, with validation 91.80/94.53/93.55%. Its p1 has 40 false blocks and 21 misses. Fitting examples suggest over-inference of sexual content or criminal intent from vague creative requests, plus missed real-person health information. One candidate clarifies these evidence and privacy boundaries; the other tests a shorter version that explicitly includes harmful endorsements. Broadening privacy to health discussed publicly is a policy-scope hypothesis and could create false blocks; it is not a neutral formatting change. Several source labels appear questionable without context; labels are preserved and no names or individual exceptions are inserted.

All five pilots returned valid labels and complete score coverage. The 27B and 35B-A3B pilot accuracies were both 93.36%. Shared-policy fitting runs also have zero output failures so far. Repeated calls can still differ under batching despite greedy decoding; the final analysis will report the identical-request pilot/search diagnostic without treating it as a controlled repeatability experiment.

Qwen 35B-A3B's p0/p1/p2 fitting accuracy is 92.87/92.87/93.07%. The p2 parent has 45 false blocks and 26 misses. Its drafts test action-and-object evidence (rather than inferring harmful context from vague language), with explicit benign transformation and safety-work exceptions. The second tests a compact rule that also counts direct harmful endorsements and abusive content in the input. These drafts were based on fitting/pilot errors, not individual validation examples. All ten new candidates are now registered, bringing the search to five candidates per model: 25 model/candidate configurations and 13 distinct policy texts.

## Tailored-candidate outcomes: first two sizes

Both new 2B candidates underperform its original shared checklist: p3/p4 validation accuracy is 86.91/85.94%, compared with p2 at 87.70%. The corresponding fitting accuracies also fall to 84.77/83.69%. For 4B, p3/p4 validation is 89.65/88.87%, below p1 at 91.02%; fitting falls to 89.26/89.55% from p1's 91.80%. These are retained negative results. The candidate budget is closed: no further revisions will be written in reaction to these scores. This helps distinguish limited prompt search from a guaranteed improvement story.

## Validation selection and pre-test freeze

All 55 pilot/search/validation runs completed. Candidate editing is closed. Each model evaluated p0, p1, p2 and exactly two fitting-derived drafts. The selected configurations below maximize validation accuracy; no new Qwen test or audit inference had begun when the freeze was created. Prior specialist test results remain known, so this is exploratory.

| Model | Selected policy | Validation accuracy |
|---|---|---:|
| Qwen/Qwen3.5-2B | wg-p2-boundary-checklist | 87.70% |
| Qwen/Qwen3.5-4B | wg-p1-concrete-harm | 91.02% |
| Qwen/Qwen3.5-9B | qwen-9b-p3-social-and-sensitive-boundaries | 94.14% |
| Qwen/Qwen3.5-27B | wg-p1-concrete-harm | 94.53% |
| Qwen/Qwen3.5-35B-A3B | qwen-35b-a3b-p4-compact-content-and-purpose | 94.53% |

The freeze records every final policy/model/source/data hash, fixed decoding settings and each available validation-derived label-score threshold. Primary results will use strict free-generated labels. p0, shared p2 and selected configurations are all evaluated on test and audit, reusing identical configurations. No prompt editing or test-based threshold selection is permitted.

For 35B-A3B, the compact p4 ties p1 at 94.53% validation accuracy and wins the registered shorter-text tie-break. This is not a validation accuracy improvement. The 9B p3 wins by two validation examples over shared p2. The other sizes select inherited prompts. All ten new drafts remain in the record, and no further edits were made. Fourteen distinct final configurations produce 28 final runs because 2B's selected and shared policies are identical.

## Analysis clarification during final inference

The registered threshold controls already compare validation-calibrated initial and selected policies. The analysis now also emits explicit paired intervals for selected free labels versus the calibrated initial policy, and for selected-calibrated versus initial-calibrated predictions. This makes the prompt-versus-operating-point comparison directly reproducible. It is a secondary analysis added after some new test scores were visible; it changes no prompt, threshold, inference setting, primary comparison or test population. All five models receive the same diagnostic.

## Inference complete and compute terminated

All 83 runs completed, producing 70,634 classification outputs across repeated model/prompt evaluations. Every registered test configuration has all 1,699 labeled official-test rows and every audit configuration has all 512 audit rows. All outputs parse as valid labels; there are zero output errors. Source population metadata, prompt hashes, settings, model/policy revisions, metrics and freeze bindings were verified for every run. A local verification-helper JSONL parsing bug was corrected before this check; inference code and recorded predictions were unchanged.

The private archive contains 525 files, 36,649,454 bytes, SHA256 `16f5cc98d4ad61c7866c51d54da60ee861da4b3baaac97a339df97bc5fef5792`. It includes raw requests/responses, inference source, job files and full logs and is retained outside the repository. The GPU was terminated after collection, and its temporary provider/local SSH key was removed. Provider usage is 3,690 GPU seconds at $1.99/hour, charged $2.04; cumulative experiment spend is $7.91 including the previous $5.87. Final analysis and public score reproduction run locally after termination.

## Findings and publication

Selected Qwen test accuracies are 83.05% (2B), 87.58% (4B), 89.58% (9B), 91.29% (27B), and 90.29% (35B-A3B). The two smallest specialists outperform their nearby Qwen comparators in the exploratory paired intervals; this remains true under available frozen threshold controls. Qwen 27B exceeds the recorded Safeguard deployment, but its advantage over CoPE is uncertain. Other larger-model nearby-size comparisons also have intervals crossing zero.

Prompt-selection gains over initial Qwen are +3.12, +1.94, +0.53, +1.88 and 0.00 percentage points. The new 9B candidate's small validation gain transfers to a small, uncertain test gain. The 35B candidate wins its validation length tie but adds no test accuracy. For 2B, the calibrated initial policy reaches 82.93%, nearly the selected free-label score of 83.05%; for 4B, selected wording still exceeds its calibrated initial policy. Secondary paired contrasts are labeled as added during final inference, with no changes to primary outcomes.

The exported figure was visually reviewed; its legend was moved to avoid covering data. This cosmetic change affects no analysis. All public result tables are generated from analysis.json. The original WildGuard code and published evidence remain unchanged.

CPU reproduction succeeded for all 83 runs / 70,634 predictions, including every metric and paired interval. The archived Python/JSON analysis and inference sources were checked byte-for-byte against the sources used for reproduction. Provider billing was rechecked after termination and remained $2.04. The public artifacts contain no source prompts or raw traces. Final results, plots, prompt histories, methodology, costs and a plain-language readout are published together for future articles and a research report.
