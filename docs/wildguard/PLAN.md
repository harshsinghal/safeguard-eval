# WildGuard policy optimization study

Protocol v1, registered 2026-10-24 before dataset inspection or inference. Status: implementation and access checks. This is a reproducible experiment, not a promise of a favorable result.

## Question and scope

Can a frozen custom-policy classifier, using a written policy optimized on WildGuardTrain, outperform the released WildGuard checkpoint on unseen WildGuardTest prompt-harmfulness labels? The clean within-model comparison is initial versus tuned policy. Cross-model differences cannot establish that policy tuning is generally superior to weight training: architectures, sizes and training exposures differ, and the policy models themselves have been trained.

Phase 1 uses prompt harmfulness only: harmful = BLOCK, unharmful = ALLOW. No REVIEW class. Missing labels are excluded and counted. Assistant responses and category/adversarial metadata never enter model requests. Response harmfulness and refusal remain future experiments.

## Models and main comparisons

- Released allenai/wildguard 7B with its official three-line classifier format, empty assistant response, greedy decoding, and no policy tuning (one baseline).
- openai/gpt-oss-safeguard-20b, musubilabs/policylm-1.7b, zentropi-ai/cope-b-a4b, mistralai/Shieldstral-1.0-3B.
- Each policy model: substantive initial taxonomy policy; one shared tuned policy; independently tuned policy (12 configurations).
- Models, tokenizer revisions, adapters and decoding remain fixed during tuning. Score-based adapters use threshold 0.5 in the primary comparison. Threshold calibration is a separately labeled validation-only control. No test-derived thresholds.

## Data isolation

Pin the official dataset revision and source hashes. Prepare WildGuardTrain only, excluding null prompt labels. Group exact normalized duplicates and near duplicates using word 5-shingle MinHash candidate retrieval and verified Jaccard >=0.85; related rows remain together. Allocate groups deterministically into approximately 80% fitting, 10% validation, 10% internal audit, balancing label, adversarial and category strata where possible. Publish assignment IDs and summary counts, not gated source text. Report label conflicts without relabeling.

These internal partitions are held out from our optimizer, not from WildGuard's original training. Official WildGuardTest is untouched until policies and settings are frozen. Retain the official test population, including repeated prompts; perform train/test overlap and deduplicated sensitivity analysis after freezing. Test filtering follows official evaluation: prompt_harm_label must be non-null, response is empty.

## Policy search

Start with a credible policy covering all 13 WildGuard risk subcategories and clear benign exceptions. Optimize accuracy, not cherry-picked examples. Use fixed, stratified, group-selected fitting samples for cheap search. A 256-row/model training-only pilot measures adapter validity, batching, throughput and cost. Sampled training results must never be described as full-training accuracy.

Maximum search allowance: three rounds with two new candidates per round for shared search, then the same allowance for each per-model search. A smaller search is permitted for budget feasibility and must be logged before execution. Candidate changes arise only from fitting-set error patterns. Shared search objective is equally weighted mean fitting accuracy across the four models. Each candidate has an immutable file, rationale, parent, change description, SHA256, fitting score and validation score. Do not copy training prompts into policy text or add row-specific exceptions. Policy <=1,500 words. No weight changes or demonstrations.

Use validation to select the final shared and per-model policies (ties: shorter policy, then lexicographic ID). Policy-specific selection considers initial and all evaluated candidates, so a non-improving candidate does not replace the initial policy. Expand fitting evaluation for finalists, preferably full fit partition if affordable. Audit is evaluated once after freeze. Select the primary model/policy on validation before opening test. Publish every completed comparison and all unsuccessful candidates, with any departures from the 13-configuration plan explicit.

## Freeze and scoring

Freeze an immutable manifest containing policies, selected candidates, model revisions, source hashes, dataset assignments, decoding, thresholds and scoring before test inference. Test execution refuses missing/changed freeze artifacts. No policy editing after test inspection within this study version.

Primary metric: row-weighted accuracy, parsing/runtime failures counted incorrect and reported separately. Secondary: harmful-class F1, binary macro F1, harmful recall, benign false-positive rate, confusion matrix, adversarial/vanilla/category slices, latency, tokens and cost. For compatibility also reproduce the official evaluator's harmful F1 convention that treats parsing failures as incorrect binary predictions. Report paired group-bootstrap 95% intervals for accuracy deltas against WildGuard and against the same model's initial policy; include paired discordant counts. Confidence intervals do not remove selection bias or benchmark contamination. No claim of a winner if the evidence is uncertain.

Threshold calibration is separate from policy wording: choose threshold on validation only, show initial, tuned, and tuned+calibrated. WildGuard receives the same option only if reliable compatible scores are implemented; otherwise explain the missing control and do not mix it into the primary comparison.

## Budget and execution

Prior GPU spend: $1.57. Existing user cap: total strictly below $10; at most $8.42 additional with a small reserve. GPU.ai first; Runpod is authorized as fallback when credits/capacity require it. Provider credits do not increase this cap. Check prices and available credit before provisioning. Keep provider/API keys local, stage only the Hugging Face download credential if necessary, redact logs, use localhost inference, bounded jobs, automatic shutdown and explicit instance deletion. Retrieve artifacts before terminating and verify provider billing and deletion. Never leave an idle paid GPU while planning.

The full study may exceed the remaining budget. The pilot sets the feasible scope. Prioritize complete official-test coverage for finalized comparisons over search breadth. If the cap prevents the entire study, preserve completed evidence and clearly mark unfinished comparisons; do not silently shrink the test set or fabricate final results.

## Evidence and writing archive

Maintain NOTES.md as a timestamped lab notebook, RESULTS.md as the current evidence ledger, and a machine-readable progress file. Record decisions, failures, adapter checks, candidate deltas, every invocation, dependency versions, GPU/driver/runtime, immutable predictions, validation selections, freeze, billing and limitations. Keep raw gated data and credentials outside Git. Public results contain IDs, labels, scores and hashes; avoid republishing gated prompts. Preserve source snapshots alongside run artifacts.

Future outputs: tutorial on policy design; technical article on failure modes and calibration; research-style report with hypotheses, preregistered method, all results, uncertainty, compute budget, data/model cards, limitations and negative findings. Draft only evidence-backed claims after experiments.

## Progress checklist

- [x] Save protocol and research documentation structure.
- [ ] Verify dataset/model access; pin revisions and fetch training data.
- [ ] Build grouped partitions, audit duplicates/conflicts and save provenance.
- [ ] Implement binary adapters, bounded batched runner, search records, scoring and freeze checks.
- [ ] Test leakage barriers, scoring, adapters and reproducibility locally.
- [ ] Run training-only pilot on all five models; record cost/throughput and feasible scope.
- [ ] Evaluate initial and candidate policies; record training errors and edits.
- [ ] Select shared and per-model policies using validation; freeze settings.
- [ ] Run frozen internal audit and official WildGuardTest comparisons.
- [ ] Review errors, intervals, overlap and calibration controls.
- [ ] Collect artifacts, terminate compute, reconcile billing and publish evidence.

## Primary sources

- https://huggingface.co/datasets/allenai/wildguardmix
- https://huggingface.co/allenai/wildguard
- https://github.com/allenai/safety-eval/tree/main/evaluation/tasks/classification/wildguardtest_prompt
- https://github.com/allenai/safety-eval/blob/main/src/classifier_models/wildguard.py
- https://arxiv.org/abs/2406.18495
