# General-purpose Qwen versus policy-specialized models

## Question and status

Can a general-purpose instruction model classify WildGuard prompt harmfulness as accurately as a nearby-size policy model when both receive the same rules, and does training-error-driven prompt tuning help it? This is a follow-up to the completed WildGuard policy study, not a fresh confirmatory test: the experimenter has already seen WildGuardTest results. No model weights will be updated.

## Registered comparisons

| Existing model | General-purpose comparator | Matching rationale |
|---|---|---|
| PolicyLM-1.7B | Qwen3.5-2B | Nearby dense language-model size |
| Shieldstral-1.0-3B | Qwen3.5-4B | Nearby dense language-model size |
| WildGuard 7B | Qwen3.5-9B | Nearby dense language-model size |
| CoPE-B-A4B (25.2B total, 3.8B active) | Qwen3.5-27B and Qwen3.5-35B-A3B | Separate total-size and active-parameter comparisons |
| GPT-OSS Safeguard-20B (about 20.9B total, 3.6B active) | Qwen3.5-27B and Qwen3.5-35B-A3B | Approximate total-size and active-parameter comparisons |

Qwen names describe language-model sizes. Its checkpoints also contain vision-related parameters; report full checkpoint counts from pinned Hugging Face metadata. Text inputs only. Dense and mixture-of-experts models are not compute-equivalent, and similar parameter count does not control architecture, training data, age, or training compute. These comparisons do not isolate the causal effect of safety specialization. No claim that policy models are generally unnecessary follows from this one task.

Five unique new checkpoints are evaluated. The two larger checkpoints each serve two registered comparisons; their results are not independent repetitions. Original policy-model predictions are reused with their recorded revisions/runtime. Do not claim a controlled speed ranking across the historical and new runs.

## Data and search

Reuse exactly the previous grouped 1,024 fitting and 512 validation rows, plus the full 1,699 labeled official-test rows and 512 internal-audit rows. Dataset revision, IDs, hashes and label mapping remain unchanged. Categories are not held out: this tests different prompts in the same broad harmfulness taxonomy. Source responses, labels, categories and adversarial flags never enter requests. No REVIEW class.

Each Qwen model evaluates the existing p0, p1 and p2 policy texts. Then the assistant writes at most two model-specific candidates using only fitting mistakes, with no copied examples, identifiers, entity-specific rules or demonstrations. The full policy remains at most 1,500 words. Aggregate validation scores may guide selection, but validation prompts and individual mistakes may not guide edits. There are five candidates per model, matching the previous study's candidate count; inherited shared policies and prior benchmark knowledge prevent a claim of perfectly matched search effort.

Select each model's policy by validation accuracy; ties prefer shorter policy text, then lexicographic ID. Save all fitting/validation scores, unsuccessful edits and rationales. Freeze selection, policy hashes, source hashes, revisions, settings and dataset hashes before any new Qwen audit/test inference. Do not select the overall winner after test or revise policies using test feedback. The final configurations are p0, the original shared p2, and the Qwen-selected policy, reusing identical configurations.

## Classification and controls

Render the policy's purpose, block, allow and precedence fields as a system instruction. The user message contains only a JSON-encoded request to classify. Keep the system wrapper identical across Qwen sizes and candidates. Explain that ALLOW maps to A and BLOCK to B; require exactly one letter. Parse the complete free-generated final answer strictly. No constrained decoding, refusal-to-BLOCK shortcut, retries or hidden label repair. Output failures count as incorrect.

Primary deployment: official post-trained Qwen3.5 checkpoints, BF16, text-only use, explicit `enable_thinking=false`, temperature zero, maximum eight output tokens, concurrency 32, pinned vLLM. Qwen's recommended sampling defaults differ; this is a fixed greedy classification deployment, not a claim of each model's maximum possible performance. Reasoning mode is not included in this budgeted study. Historical Safeguard used medium reasoning and MXFP4; make this deployment mismatch explicit.

Collect unconstrained A/B token probabilities where available. As a separate control, choose a cutoff on validation over 0.01–0.99 (ties closest to 0.5, then lower), retaining output failures. Never reinterpret an invalid answer as a successful classification. If valid-answer score coverage is incomplete, mark calibration unavailable instead of selecting a favorable subset. Scores are conditional label-token scores, not calibrated probabilities of harmfulness.

Primary metric: accuracy. Also report harmful-class F1, macro F1, harmful recall, benign false-block rate, output failures, adversarial/vanilla slices and category slices. Use paired group-bootstrap accuracy intervals and discordant counts on matched IDs, with the existing 2,000-replicate seed. All comparisons are exploratory and unadjusted for multiplicity. Show p0-versus-p0 and shared-p2-versus-shared-p2 comparisons where applicable, then independently selected-versus-selected configurations. WildGuard remains a fixed baseline without custom policy text.

## Budget, operations and documentation

Existing cumulative spend is $5.87. Preserve the user's original cap strictly below $10. Maximum new planned spend is $4.12; reserve headroom. GPU.ai first and Runpod only as an affordable fallback. Rent no GPU before the local runner, protocol and smoke checks are ready. At $1.99/hour use a two-hour provider cutoff (maximum nominal $3.98), retrieve artifacts continuously, stop new work in time to collect and terminate, and verify final billing. Shorten scope transparently if capacity/runtime prevents completion; never silently sample the official test or exceed the cap.

Preserve private raw requests/responses, exact source/policy/model versions, runtime, costs, failures and all candidate scores. Publish prompt-free predictions, methods, paired analyses and a readable report. Extend the writing/claims map only with evidence from completed comparisons. This study can show whether Qwen is a competitive classifier on this benchmark; arbitrary-policy adherence, new categories and downstream protection need separate experiments.

## Progress

- [x] Verify candidate model sizes and record comparison limitations.
- [x] Pin models, implement adapter and verify leakage/output/scoring checks.
- [x] Publish protocol before new paid inference.
- [ ] Run fitting-only pilots and shared policy evaluations.
- [ ] Write and evaluate fitting-derived candidate prompts.
- [ ] Select on validation and freeze all new comparisons.
- [ ] Run complete official-test and internal-audit comparisons.
- [ ] Collect, terminate compute, reconcile billing and reproduce public results.
- [ ] Publish plain-language findings and research evidence.

## Primary sources

- [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B), [4B](https://huggingface.co/Qwen/Qwen3.5-4B), [9B](https://huggingface.co/Qwen/Qwen3.5-9B), [27B](https://huggingface.co/Qwen/Qwen3.5-27B), [35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B).
- [CoPE-B-A4B architecture](https://huggingface.co/zentropi-ai/cope-b-a4b).
- [Prior methods and model exposure](../wildguard/METHODS.md), [prior results](../../published_runs/2026-10-24-wildguard/README.md).
