# WildGuard lab notebook

Append dated entries; retain failed attempts and protocol deviations. Do not include credentials or gated prompt text.

## 2026-10-24 — protocol and access

The user authorized implementation, supplied Hugging Face and Runpod credentials in the local KEYS directory, and requested durable research notes. The earlier total spending cap remains $10; prior billed compute is $1.57. Existing arena results are exploratory and do not answer the WildGuard policy-tuning question.

Protocol saved before new inference. Hugging Face model config access succeeds. Dataset repository metadata is accessible; file access and pinned download are next. No paid resources have been created for this study. Existing GPU.ai instance list is empty.

## 2026-10-24 — dataset preparation and adapter decisions

Pinned dataset revision d29c47f41c8b51348b5c8e8c81c039b3132b66d1; training parquet SHA256 02ecea8a724a9146a1e473a95a7cdf262adfe9c7d5408953ca86d2fcfbdc8953. All 86,759 training rows have binary prompt labels. Fourteen prompts are empty strings (13 unharmful, one harmful); retained as valid source rows and grouped together, rather than silently removed. An initial strict nonempty check caught these before inference and was corrected to preserve population.

Training partitions: 69,366 fit, 8,700 validation, 8,693 audit. Exact and approximate near-duplicate grouping details and strata are in data-manifest.json. Approximate retrieval does not guarantee all semantic duplicates were found. The official test has not been fetched.

Initial policy p0 covers the original taxonomy and benign exceptions. WildGuard uses official completion format and one tokenizer-added BOS. All policy models use binary ALLOW/BLOCK; native score thresholds are 0.5. PolicyLM retains upstream cleaner/windowing, fixes max_batch_rows=1 for reproducibility, and disables the character cap to avoid silently truncating long prompts. This adapter choice is fixed before observing pilot results. Safeguard uses medium reasoning with a 4,096-token cap and a short JSON reason; cap exhaustion counts as ERROR. HTTP concurrency is 32.

GPU.ai credit balance was $23.80, but the study still respects the earlier total spending cap. RTX PRO 6000 96GB offer 27740f2244eb is $1.99/hour and was reliable in the earlier run; a four-hour provider termination limit bounds new instance compute to $7.96. No Runpod spend is needed while GPU.ai credit suffices.

## 2026-10-24 — reproducibility checks before pilot inference

There are 47,804 unique normalized training prompts and 47,617 connected groups after verified near-duplicate joins; 16 groups contain conflicting labels. The 86,759-row total therefore substantially overstates independent prompt count. All paired responses remain within one partition, and all source rows remain in row-weighted scoring.

A full-file read caught embedded Unicode line separators: Python splitlines() can split inside a valid JSON string when non-ASCII text is preserved. Readers now split only on physical newline; a regression test preserves U+2028 and U+0085. This fixes ingestion without altering prompt content. Full training prompt lengths are median 242 characters, p99 2,108, maximum 12,814.

Protocol and initial implementation were committed as 3040156 and pushed before inference results existed. GPU.ai instance gpu-2b927402 started 2026-10-24T20:18:01.843635Z with automatic termination at 2026-10-25T00:18:01.843635Z. Environment installation and model downloads are billable overhead and will be included in study cost.

## 2026-10-24 — first pilot result and WildGuard compatibility repair

PolicyLM p0, 256 fitting rows: 228/256 correct (89.0625%), no parsing/runtime errors, 5.28 seconds measured inference wall time (48.52 rows/s). There are 19 false blocks and nine missed harmful requests. These are fitting-sample results, not validation or test results.

Training-only error inspection suggests overblocking harmless fictional identities, game mechanics, non-explicit creative writing, and benign requests wrapped in jailbreak-like language. Missed harms include recommendations facilitating wrongdoing, sensitive real-person information, and reproduction of protected works. Exact evidence remains in private fitting traces; no training examples or entity-specific exceptions will be copied into policies.

WildGuard's first server launch failed before predictions because vLLM 0.31.0 has removed tokenizer_mode='slow'. Repair: compute input IDs with the pinned transformers 4.57.6 slow tokenizer (SentencePiece 0.2.2), including one BOS, then submit those IDs to the vLLM completion endpoint with additional special tokens disabled. The server may use its default tokenizer for decoding; the requested input IDs preserve the official preprocessing. All failed setup time remains in billing. The incomplete phase is retained and only unrun models are resumed.

Policy tuning will edit block, allow and precedence rules, the three fields consumed by every adapter. Task/output scaffolding remains fixed. Native PolicyLM does not separately consume purpose/review fields.

## 2026-10-24 — shared candidate drafts before search

Drafted two shared candidates from p0 and fitting-only pilot error patterns. p1 explicitly separates concrete harmful outcomes from superficial jailbreak framing and spells out benign fiction/game/placeholder exceptions. It also expands facilitation beyond procedural instructions to recommendations, planning and evasion. p2 expresses the same taxonomy as an outcome checklist with a shorter precedence rule. Both preserve task/output scaffolding; neither includes dataset text, entity names, source IDs or row-specific exceptions. These drafts have not yet been selected or tested. Larger fitting/validation runs will decide whether either is an improvement.

Further startup repair: the new runtime attempted an unauthenticated metadata fetch even though gated weights were cached. Serve pinned local snapshot paths in offline mode. Convert WildGuard's tokenizer for server-side output decoding only; verify its vocabulary exactly equals the original slow tokenizer. Input IDs still come from the original slow tokenizer. Added missing SentencePiece and protobuf dependencies; record their versions in the runtime freeze. The download credential was removed after checkpoints downloaded.

## 2026-10-24 — WildGuard pilot succeeds

WildGuard with official slow-tokenizer input IDs matched 255/256 fitting labels (99.6094%), with zero parsing errors, in 27.75 seconds inference wall time. This is training data used for WildGuard's weight training, so the high score is expected and is not evidence about unseen generalization. The corrected tokenizer vocabulary match is recorded separately. The remaining policy-model pilots continue.

## 2026-10-24 — pilot completed; budgeted search scope fixed

All five initial pilots completed on the same 256 fitting rows:

| Model | Correct | Accuracy | Errors | Measured inference rows/s |
|---|---:|---:|---:|---:|
| WildGuard | 255/256 | 99.609% | 0 | 9.23 |
| PolicyLM | 228/256 | 89.062% | 0 | 48.52 |
| Shieldstral | 244/256 | 95.312% | 0 | 235.93 |
| CoPE | 240/256 | 93.750% | 0 | 37.22 |
| GPT-OSS Safeguard | 234/256 | 91.406% | 5 | 3.90 |

Safeguard's five failures all exhausted the 4,096-token cap with no final answer. Before the main comparisons, raise its cap uniformly to 8,192 for every policy; repeat the full Safeguard pilot, retain the original failures, and do not retry selected errors only. The primary study uses the new fixed cap. No other decoding or policy scaffolding changes. This is a pilot-driven protocol amendment, before validation or test access.

Budgeted search: one shared round with two candidates (p1,p2) plus p0, each on 1,024 fitting and 512 validation rows; one per-model round with up to two candidates per model, on the same examples. These sizes replace the maximum three-round allowance, not the official test population. Finalist fitting estimates will expand if budget allows; full fitting accuracy across all configurations is not feasible at the measured reasoning-model rate. Preserve complete official-test coverage as the priority. Internal audit may use the registered 512-row budget sample; any such limitation must accompany the results. Primary selection uses validation only. All sample sizes and omitted full-partition passes remain explicit.

## 2026-10-24 — pilot error patterns across models

Beyond PolicyLM's false blocks, CoPE, Shieldstral and Safeguard miss some harmful objectives embedded in benign-looking stories: operational cyber abuse, evasion/fraud, sensitive data requests, group stereotypes, and manipulative or degrading content. Conversely, some benign benchmark examples contain suspicious or risky wording. This makes the fiction boundary a trade-off, not a universal allow-list. Candidate selection must show both harmful recall and benign false-positive rate alongside accuracy. No source labels are changed to accommodate model judgments.

Five pilot errors on Safeguard are length-cap failures with 4,096 completion tokens and empty final content, rather than malformed JSON. Main search uses 8,192 uniformly; the repeated full pilot is a separate run ID.

## 2026-10-24 — first negative policy result

On the fixed 1,024-row fitting sample, PolicyLM p0 scores 88.379% (83 false blocks, 36 missed harms). Candidate p1 scores 84.375% (154 false blocks, six missed harms). Adding detailed benign exceptions alongside broader harm rules did not make the classifier more permissive: harmful recall rose, but false blocks nearly doubled. Validation accuracy also fell, from 90.234% to 86.914%, though future edits will still be based on fitting errors only. Retain this unsuccessful candidate. A longer or apparently clearer policy is not automatically a better model input.

## 2026-10-24 — PolicyLM's second shared candidate and specific edits

Shared p2 improves PolicyLM fitting accuracy to 91.992% (33 false blocks, 49 missed harms), compared with p0's 88.379%. Its validation accuracy is 90.039%, one case below p0's 90.234%. This is an early example of a fitting gain that does not yet establish validation improvement.

Model-specific drafts p3/p4 use only fitting errors. p3 expands copyright reproduction and real sensitive-record boundaries, clarifies the breadth of social-group stereotypes, and avoids inventing harmful context in incomplete messages. p4 is a compact version of the taxonomy to test whether fewer overlapping instructions help the small classifier. These are hypotheses, not corrections to the benchmark labels. All full texts and hashes will be registered before inference.

## 2026-10-24 — Shieldstral shared improvement and specific candidates

Shieldstral p2 reaches 98.438% on both the 1,024 fitting and 512 validation samples, versus p0's 95.605% / 95.508%. Fitting errors: two false blocks and 14 missed harms. Several remaining misses are short, context-dependent source messages; we will not add lexical exceptions for those IDs. p3/p4 instead test general boundaries around disguised harmful deliverables, stereotypes, sensitive records, operational abuse and unhealthy dependence, while preserving benign fictional/game exceptions.

CoPE p1 slightly improves fitting accuracy (93.262% to 93.652%) but lowers validation accuracy (94.336% to 93.164%). This is another candidate to retain as negative evidence. Its remaining fitting misses cluster in social-group stereotypes, deceptive influence, and harmful objectives framed as fiction or research.

## 2026-10-24 — CoPE-specific hypotheses

CoPE p2 is the best shared candidate on fitting accuracy (93.848%, versus p0 93.262%), but validation remains slightly lower (93.945% versus p0 94.336%). Specific p3 expands the definition of social-group discrimination and deceptive/degrading deliverables. Specific p4 tests whether the policy should explicitly cover harmful statements or endorsements already present in the user text, as well as requests for a harmful answer. This is a substantive scope hypothesis drawn from fitting errors, retained transparently; it may improve recall at the cost of false blocks. Neither policy includes dataset identifiers or copied prompts.

## 2026-10-24 — larger reasoning cap does not remove the failure mode

The separate 8,192-token Safeguard pilot scores 237/256 (92.578%) but still has six exhausted-output failures, versus five in the 4,096-token pilot. A larger cap therefore does not reliably solve the issue. Temperature is zero, but dynamic batching and floating-point execution can change token trajectories; this is not a controlled repeatability study. Keep 8,192 fixed for all main-study policies and report every failure. Do not silently retry or drop difficult items.

The question concerns test examples held out from our policy optimizer. Public benchmark exposure in the policy models' original training is unknown; no claim of uncontaminated model-level generalization is justified.

## 2026-10-24 — interpretation safeguards

The binary source labels measure agreement with WildGuardMix annotators, not an independently established universal notion of harmfulness. Some fitting messages lack context; we retain the original labels and avoid adding memorized exceptions. The error-inspection helper explicitly refuses non-fitting runs. Validation is used through aggregate metrics for selection; its prompts and individual errors do not inform edits.

Main-study runtime comparisons will include cold setup/download cost separately. Pilot throughput can substantially understate warm inference throughput because first-use kernel work occurs inside the first measured run. Latencies from different adapters and generation lengths should not be treated as a controlled speed benchmark.

## 2026-10-24 — main Safeguard baseline

Safeguard p0 on 1,024 fitting rows: 91.113% accuracy with 12 errors under the fixed 8,192-token cap. Failures remain in the denominator. This establishes the main-study baseline; the earlier 256-row pilot is not substituted for it. Fitting errors include 34 benign false blocks, missed harmful objectives across several categories, and twelve exhausted/invalid outputs. We are waiting for p1/p2 before selecting a parent for model-specific edits.

## 2026-10-24 — exploratory validation uncertainty

For shared p2 versus p0 on the same 512 validation rows (495 groups), the paired group-bootstrap accuracy differences are: PolicyLM -0.195 percentage points, 95% interval [-2.165, +1.765]; Shieldstral +2.930 points, [+1.572, +4.510]; CoPE -0.391 points, [-1.754, +0.971]. Shieldstral corrected 15 cases without breaking a previously correct case in this sample. These are exploratory intervals on selection data, not independent confirmation and not adjusted for trying several candidates. Frozen official-test comparisons will carry the main inference.

## 2026-10-24 — reasoning failure diagnostics

The six 8,192-token Safeguard pilot failures show severe repetitive generation: only 1.46%–4.64% of word 5-grams are unique; the most repeated 5-gram occurs 3,807–4,003 times. This is output degeneration, not merely a thoughtful answer needing a slightly larger budget. Root cause (model, decoding, quantization or runtime interaction) is unresolved. Preserve the diagnostic artifact and treat the comparison as performance of this documented deployment. Do not claim these failures establish an intrinsic limit of the model. Main decoding remains fixed; a future decoding/runtime ablation is separate from this policy-only study.

## 2026-10-24 — Safeguard specific candidates registered

Safeguard shared p1 slightly improves fitting accuracy to 91.699% and reduces output errors from 12 to four, while increasing missed harmful requests. Before seeing p2 scores, register p3 (from p1) and p4 (from the checklist design) using p0/p1 fitting errors and pilot inspection. Both distinguish actual prohibited deliverables from benign fictional/game/analysis content; p3 spells out exceptions and disinformation/stereotype scope, while p4 tests a concise evidence-based boundary and harmful content already present in the message. Output format, reasoning level and cap remain unchanged. This completes the predeclared two model-specific candidates per model; no more candidates will be added in this study.

## 2026-10-24 — disclosed training exposure

PolicyLM's official card explicitly says its PolyGuardMix training source includes WildGuardMix. Exact overlap with source splits is unverified, and we have not established test contamination. This strengthens the need to frame results as no additional weight updates in our experiment, not as untrained policy models versus a trained baseline. Shieldstral's public report uses heterogeneous safety data and reports this benchmark, but does not establish source-row exclusion in the sections reviewed. CoPE describes disjoint internal data; that is not proof of disjointness from WildGuard. The model-exposure note records the sources and limits before official-test access.

## 2026-10-24 — final evaluation scope before policy selection

The shared search is complete. Model-specific candidates are running, with no further edits permitted. Main results retain the fixed 0.5 score threshold. Before opening official test, separately choose validation-accuracy thresholds on a fixed 0.01–0.99 grid for each selected score-based policy, including p0. Ties prefer proximity to 0.5, then the lower threshold. Freeze those values with the policy selection. This permits both threshold-only (p0 calibrated) and policy-plus-threshold secondary controls; neither changes the primary model or primary fixed-threshold comparison. WildGuard and Safeguard do not expose comparable scores in these adapters.

Register the final fitting estimate on the existing 8,192-row fitting sample for every unique final configuration and WildGuard, subject to the original budget. This is not full-training accuracy (the fitting partition has 69,366 rows). Evaluate the full official task-specific test population and the 512-row internal audit sample first, then the expanded fitting sample. The study will report omissions if the hard deadline prevents completion. Final fitting scores cannot change selected policies. A shared and individual role using the same policy reuses one inference run, rather than presenting it as two independent repetitions.

The full original maximum search (three rounds) was not attempted: this is a bounded one-round shared plus one-round model-specific study. The 11 retained policy files and all unsuccessful trials are part of the evidence.

## 2026-10-24 21:13 UTC — policy and threshold freeze, before official test download

All 20 policy-model search configurations and the WildGuard baseline completed matched fitting/validation runs. The shared winner is p2 (boundary checklist). Individual winners: PolicyLM p4 compact (91.797% validation), Shieldstral p4 taxonomy priority (98.633%), CoPE p3 social/deception (95.313%), Safeguard p2 checklist (92.578%). Safeguard p1 ties p2 in validation accuracy; p2 wins the predeclared shorter-policy tie-break. Its specific p4 improves fitting accuracy but loses validation, so it is not selected.

The primary comparison is Shieldstral p4 versus official WildGuard, selected without test access. There are 12 unique final configurations: one WildGuard, three each for PolicyLM/Shieldstral/CoPE, and two for Safeguard (shared and individual roles coincide). The selection, nine validation-only threshold controls, full candidate scores and immutable source/model/policy/data freeze are saved under published_runs/2026-10-24-wildguard. Freeze creation time is recorded in freeze.json; it will be committed and pushed before test download. All policy editing is closed.

The primary threshold remains 0.5. Secondary selected thresholds are PolicyLM p0/p2/p4: 0.54/0.32/0.44; Shieldstral p0/p2/p4: 0.14/0.46/0.50; CoPE p0/p2/p3: 0.50/0.06/0.08. These sometimes large shifts make the calibration control informative, but they may overfit 512 validation rows. No threshold is selected on test results.

## 2026-10-24 21:14 UTC — official test opened after freeze commit

Freeze commit e190b01 was pushed to GitHub before the authenticated test download. The pinned source contains 1,725 rows; 1,699 have prompt-harmfulness labels and 26 are excluded solely for null labels, matching the official task filter. All 1,699 are unique under the registered exact/near grouping procedure. The full labeled population is used for every frozen configuration. Source/data hashes and task population counts are recorded in the evidence package. Test and internal-audit inference have started; policy and threshold files remain unchanged. Post-freeze train/test lexical-overlap analysis runs separately and cannot filter the main evaluation.

## 2026-10-24 — chronology clarification and overlap audit

Clarify the protocol's public-registration wording: the local plan preceded inference, but its first public commit (3040156, 20:18 UTC) already included training-data preparation findings. It is therefore a pre-inference protocol with documented pilot amendments, not an externally timestamped registration before all dataset inspection. The stronger test barrier is independently visible: e190b01 freezes all policies and thresholds before official-test download.

Post-freeze lexical audit finds one exact and one near test/training match, involving two of 1,699 test rows. Neither matched training group appears in the 1,024 optimizer-fitting or 512 optimizer-validation samples. This does not establish absence of semantic overlap or absence of model pretraining exposure. The main test keeps both rows; a 1,697-row sensitivity score is reported separately.

## 2026-10-24 — primary official-test comparison

On all 1,699 labeled test rows, the preselected Shieldstral p4 scores 1,543/1,699 (90.818%) versus WildGuard's 1,535/1,699 (90.347%). The paired difference is +0.471 percentage points, bootstrap 95% interval [-0.235, +1.236]. There are 25 rows correct only for Shieldstral and 17 correct only for WildGuard. The point estimate is higher, but the interval includes zero; this study does not establish superiority over WildGuard.

Within Shieldstral, p0 scores 1,494/1,699 (87.934%). Tuning adds 49 net correct predictions (+2.884 points, paired interval [+2.001, +3.826]), with 57 corrected cases and eight regressions. Harmful recall rises from 79.841% to 86.870%; benign false-block rate rises slightly from 5.608% to 6.032%. Relative to WildGuard, tuned Shieldstral catches 14 additional harmful rows but incorrectly blocks six additional benign rows. Accuracy alone hides this operational trade-off.

PolicyLM p4, chosen on validation, scores 86.816%, versus p0 85.050%. Its shared p2 scores 87.169% on test, but we do not change the winner after test access. This difference illustrates selection uncertainty. Remaining test/audit runs and expanded fitting estimates are still in progress; no policies or thresholds are being changed.

## 2026-10-24 — complete official-test coverage and negative Safeguard result

All 12 unique frozen configurations completed all 1,699 labeled official-test rows (20,388 test predictions). Safeguard p0 scores 89.818% with 11 failures; selected p2 scores 89.641% with nine failures. Fewer operational failures did not produce a higher overall score. CoPE p3 scores 90.759%, versus p0 90.465%; its calibrated p3 secondary control scores 90.936%. These secondary results do not replace the preselected primary.

Shieldstral p0 at the validation-selected threshold 0.14 reaches 90.112%, versus 87.934% at 0.5. Policy tuning at the fixed threshold reaches 90.818%. Thus calibration alone accounts for much of the observed initial-to-tuned gain, and the report includes the remaining paired difference against calibrated p0. PolicyLM's validation-selected thresholds mostly reduce test accuracy, illustrating calibration overfit or distribution shift. No test-based threshold replacements are made.

Analysis now adds annotator-agreement slices and a descriptive failure-contribution breakdown. These are post-freeze exploratory analyses, not new primary outcomes. The official test is now observed: further policy development would need a fresh confirmatory holdout, or results must be labeled exploratory. The current study's policy selection remains closed.

## 2026-10-24 — secondary controls and error slices

The selected-policy minus calibrated-initial-policy differences are: PolicyLM +1.707 points (paired 95% interval [+0.412, +3.061]); Shieldstral +0.706 points ([-0.059, +1.530]); CoPE +0.294 points ([-0.530, +1.118]). Thus Shieldstral's residual advantage beyond simple calibration is uncertain in this sample. These controls were fixed before test; intervals are exploratory and unadjusted for multiple comparisons.

Shieldstral's gain over p0 includes nine net additional correct cyberattack cases and nine fraud/illegal-activity cases, with smaller gains across other harmful categories. It loses four net benign cases and one social-stereotype case. Because several clauses changed together, these counts cannot identify which clause caused a gain. The full category table is preserved.

The selected Shieldstral policy scores 93.80% on 903 vanilla examples and 87.44% on 796 adversarial examples; WildGuard scores 92.69% and 87.69%. The small overall advantage therefore does not imply an adversarial-subset advantage. On source labels with two-of-three annotator agreement, Shieldstral scores 81.39% (591 rows); on three-of-three agreement, 95.85% (1,108 rows). These slices describe agreement with the chosen source label, not independent adjudication of model correctness.

Safeguard's selected policy corrects six initial output failures but turns six formerly correct cases into new output failures. The reduction from 11 total failures to nine is not equivalent to a net six-case accuracy gain. A separate deployment/repeatability study is needed to isolate runtime effects.

## 2026-10-24 — expanded fitting pass and collection repair

All 24 held-out runs (12 official test and 12 internal audit) completed before the 12 expanded-fitting jobs began. WildGuard scores 99.915% on 8,192 fitting rows, with one parsing failure; that near-perfect score is on its original weight-training distribution, not new test evidence.

A live artifact sync reported that an in-progress prediction file changed while tar was reading it. The sync aborted rather than using a potentially inconsistent snapshot. Collection now archives only runs whose completed summary parses successfully; no inference was repeated or changed. The final private archive will be collected only after the entire phase completes.

Added a post-freeze descriptive consistency check between search and expanded fitting predictions for their overlapping source IDs. It will verify identical requests and report changed decisions and failure transitions. Different batch contexts mean this is a diagnostic, not a controlled repeatability experiment.

## 2026-10-24 — consistency checks on the completed non-reasoning fitting runs

For the 1,024 repeated search examples, all three PolicyLM policies, WildGuard, and Shieldstral p2/p4 reproduce identical decisions. Shieldstral p0 changes two decisions; CoPE p0/p2/p3 change two/six/three decisions. The request hashes are identical, and model/policy/source identities match. One repeated exact-prompt group within CoPE p3's expanded run also has differing decisions. These observations show inference variation under changed batching; they do not isolate its numerical cause. The bootstrap intervals resample examples and do not include this runtime variation. Safeguard's expanded runs are still in progress.

Provider dollar figures cover GPU rental only, including installation, downloads and failed setup time. They exclude local CPU/storage and assistant or human effort. Policy candidates were authored by the Codex assistant during this session; the assistant model build/token usage was not independently pinned. Exact policy texts and rationales are retained, so the evaluations can be reproduced even though identical search regeneration is not guaranteed.

## 2026-10-24 — Safeguard expanded initial-policy reliability

Safeguard p0 completes 8,192 fitting rows at 90.869% accuracy with 116 errors. Among the 1,024 requests also evaluated during search, 37 decisions change despite identical request hashes: 11 become correct, 16 become incorrect, and other changes remain incorrect. Nineteen of 606 repeated exact-prompt groups within the expanded run have differing predictions. This is a material deployment-repeatability limitation; small Safeguard policy differences must not be interpreted as stable intrinsic model differences. The selected-policy expanded run is still in progress. No unplanned decoding changes or favorable-case retries are introduced.

## 2026-10-24 22:28 UTC — all inference complete, archive validated, GPU terminated

All 84 planned runs completed: six pilots, 21 fitting-search runs, 21 validation runs, 12 internal-audit runs, 12 official-test runs, and 12 expanded-fitting runs. There are 158,628 row-level predictions, including 20,388 official-test predictions across 12 unique frozen configurations. All final populations, policies, revisions, decoding settings and inference-source hashes pass verification. There are no omitted final configurations.

Safeguard's selected p2 reaches 91.077% on 8,192 fitting rows, with 54 failures, versus initial p0 90.869% with 116 failures. On the 1,024 repeated inputs p2 changes 36 decisions (17 corrected, 15 regressed); 14 repeated exact-prompt groups have differing decisions within the expanded run. These reinforce the deployment-repeatability limitation rather than establish a reliable improvement over WildGuard.

The private raw archive contains 512 files, is 68,701,621 bytes, and passed full member hashing and archive validation (SHA256 0ffa9883d776fcc8d9a4a093973179b08c2f15229ae3211961c26ff15c4308ef). Raw inputs/responses and full logs remain private. GPU.ai instance gpu-2b927402 is confirmed terminated; the provider and local temporary SSH keys were removed. Provider-reported runtime is 7,785 GPU-seconds and cost is $4.30. Including the earlier $1.57 experiments, cumulative GPU spend is $5.87. No Runpod resources were used. The staged Hugging Face credential had already been removed after model downloads.

Final public export, score reproduction and credential/link checks follow before the results commit. GPU billing has stopped.

## 2026-10-24 — final public reproduction and release checks

The public package contains all 84 completed runs and 158,628 prompt-free prediction records. Using only the archived source snapshot and public records, the reproduction command verified every prediction archive hash, every summary metric, all paired bootstrap intervals, and all frozen threshold controls. The complete recomputed analysis matches the published analysis exactly. No GPU or dataset access was needed for this check.

Failure metadata confirms that all 20 Safeguard test output failures across initial and selected policies ended at the 8,192-token cap. Across earlier stages one Safeguard search failure instead stopped without a valid parse; the remaining recorded failures exhausted their configured cap. WildGuard has one length-cap failure in each of the search and expanded fitting runs and none on official test. These failures remain incorrect; their cause is not established.

The public-export allowlist removes generated reasons and excludes source prompts and raw traces. Publication checks found no used API/Hugging Face credentials or private-key markers and verified relative Markdown links. The frozen inference files, metric implementation, policies, registry, selection, calibration and freeze remain unchanged from the pre-test freeze commit. Final artifact checksums accompany the release. The research archive preserves all negative candidates and operational failures, and CLAIMS.md separates supported conclusions from claims requiring new studies.
