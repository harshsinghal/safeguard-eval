# Frontier models as policy classifiers

**Status: implementation and local checks complete; paid pilot awaiting a new budget. No frontier inference results yet.** This is the third study, after the specialized-policy and nearby-size Qwen comparisons.

## Questions

Can current general-purpose frontier API models improve WildGuard prompt-harmfulness classification? Does changing the written policy help them? Does additional reasoning improve accuracy enough to justify its cost and latency?

Here “foundation model” means a general-purpose, post-trained model exposed through a chat API. We are not testing raw pretrained checkpoints or updating weights. This is a benchmark of deployed classification systems, not a causal experiment on architecture or safety training.

## Core model set, checked October 25, 2026

| Model on OpenRouter | Reasoning conditions | Selected provider |
|---|---|---|
| `openai/gpt-6-astra` | Low versus high; off unsupported | OpenAI, standard endpoint |
| `anthropic/claude-opus-5.5` | Low versus high; off unsupported | Anthropic, standard endpoint |
| `deepseek/deepseek-v4.1-flash-1017` | Off versus high | DeepSeek |
| `moonshotai/kimi-k3.1-pro` | Off versus high | Moonshot AI, MXFP4 endpoint |

These are a preregistered selection of current flagship contenders, not a claim that they already top this classification benchmark. OpenAI identifies Astra as its highest-intelligence model; Anthropic describes Opus 5.5 as its new leading general-release model. OpenRouter lists Kimi K3.1 Pro as a flagship open-weight model and the October 17 DeepSeek snapshot as a newer generation that surpasses its earlier Pro tier on reported general capabilities. Those claims motivate selection, not the experiment's conclusions.

The [catalog and endpoint snapshot](catalog-snapshot.json) preserves the evidence available at selection. Kimi's catalog entry describes open weights but has no Hugging Face ID; availability of a downloadable checkpoint has not been independently verified. Models with only mandatory reasoning are not relabeled “thinking off.” Hiding reasoning text with `exclude: true` does not disable or stop billing for reasoning.

Qwen3.8-2.4T-A95B, GLM-5.3, and MiniMax-M3.1-Flash were also found in the catalog. They are possible later extensions, outside this core budget. Astra Pro is a separate compute setting of the same underlying model and is outside the core comparison. “Frontier” here identifies the model, not an unlimited-compute or maximum-effort deployment.

## Same data and search process

Reuse the exact previous files and hashes: **1,024 fitting, 512 validation, 512 internal-audit, and all 1,699 labeled WildGuardTest prompts**, at WildGuardMix revision `d29c47f41c8b51348b5c8e8c81c039b3132b66d1`. Twenty-six null-label official-test rows remain excluded. The target is prompt harmfulness only: ALLOW/unharmful or BLOCK/harmful. No REVIEW class, response-harmfulness assessment, image classification, or new category holdout is introduced.

Each of the eight model/reasoning conditions gets five policy candidates: the unchanged shared p0, p1 and p2, then two new drafts based only on its fitting errors. All five run on the entire fitting and validation samples. Candidate texts must be registered before their calls, at most 1,500 words, and must not copy examples, identifiers, names, or entity-specific exceptions. New drafts have **not** been written yet because no new fitting errors exist. Review only aggregate validation scores; never use validation or test mistakes for edits.

Select by validation accuracy, then shorter policy text, then lexicographic ID. Preserve every attempted candidate, including unsuccessful changes. Independent selection per condition estimates each deployment's tuned performance; it does not isolate reasoning by itself.

Before any new audit/test calls, publish a freeze containing exact policies, code, dataset hashes, model IDs, endpoint settings, candidate scores, and selections. For each condition, evaluate p0, shared p2, and its selected policy on both held-out populations, deduplicating identical configurations. Repeat the selected policy on the first 256 test IDs as a predeclared stability diagnostic; never use that repeat to select policies or replace primary predictions.

## Comparisons and interpretation

1. **Does reasoning help with a fixed policy?** Within each model compare higher versus lower reasoning on exactly p0, then exactly p2. Prompt wording is held constant.
2. **Does prompt tuning help?** Within each model/reasoning condition compare its selected policy with p0. Weights and inference settings stay fixed.
3. **How do tuned deployments compare?** Compare independently selected configurations, explicitly acknowledging that both wording and reasoning may differ.
4. **How do frontier results compare with prior studies?** Reuse the exact historical specialist, WildGuard, and Qwen predictions on matching IDs. Report p0/shared-p2 controls where applicable and selected-versus-selected results. Model size, age, training, precision, host, and interface differ; do not label this an equal-compute contest.

Accuracy remains primary. Report harmful F1, macro F1, harmful recall, benign false-block rate, output errors, and adversarial/vanilla and category slices. Use the existing paired group-bootstrap procedure, 2,000 replicates and seed 20261024, with discordant counts and exploratory, unadjusted confidence intervals. Report actual API charges, input/output/reasoning tokens, and latency alongside quality. No cross-model probability calibration is planned because comparable label probabilities are not universally available.

Previous WildGuardTest results are already known to the experimenter, and frontier-model training exposure to this public benchmark is unknown. Freezing before *new* test inference limits additional tuning leakage but does not create a fresh confirmatory test. This study cannot establish that specialized policy models are unnecessary or that the same results apply to arbitrary platform policies.

## API controls

The existing Qwen system wrapper renders the policy and asks for exactly A or B; the user message contains only the JSON-encoded prompt. Gold labels, source responses, categories, and adversarial flags never enter requests. Parse only the complete final answer. Refusals, explanations, and truncations count as errors; no output repair, constrained decoding, or refusal-to-BLOCK shortcut.

Use an 8,192-token total output allowance for both reasoning conditions, including hidden reasoning. This is a bounded deployment, not an assertion of maximum model performance. The fitting-only pilot checks truncation; if that cap proves unusable, amend the protocol before search and rerun all affected conditions, recording costs and failed attempts. Do not silently use an eight-token cap on reasoning models.

Omit temperature uniformly because it is not a supported control at every selected endpoint. Record provider defaults as a limitation and use the stability diagnostic. Run sequentially initially, without classification retries, with fixed provider routing, variant exclusions, required-parameter checks, and price ceilings. Record returned provider/model IDs, usage, generation IDs, timestamps, and latency. Public model IDs and catalog snapshots do not pin hidden weights; hosted deployments may change. Resolve any unexpected routing or model identity before proceeding.

Transport, routing, and billing problems stop a run; attempted failures remain in its evidence. Incomplete runs cannot enter policy selection or final comparison. A completed run's invalid classifications count as wrong. Never quietly substitute a different provider, cheaper model, shorter test, or hidden rerun.

## Budget and phase gates

Prior cumulative experimental spend is **$7.91**, leaving at most **$2.08** under the user's strict original cap. An available OpenRouter account balance does not authorize more spending. The local credential was verified through the read-only key endpoint; no paid inference was performed.

The [reproducible cost scenarios](cost-estimate.json) assume uncached input estimated from actual request lengths and the longest shared policy. At up to **116,808 requests**, the full core study is approximately **$1,144** for short reasoning, **$3,344** for moderate reasoning, or **$12,145** if reasoning is long. These are sensitivity scenarios, not quotes: provider tokenization, future prompt lengths, caching, failures, and actual reasoning lengths are unknown. Prices include reasoning as output tokens. Collection of evidence and analysis are local and incur no API charges.

**Proposed next paid phase: a new $10 pilot-only cap**, requiring the user to raise the cumulative limit to $17.91. Use the same first 32 fitting examples with p0 across all eight conditions: 256 requests. Estimated pilot cost is $2.40 with short reasoning, $7.22 with moderate reasoning, or $26.51 with long reasoning. The $10 cap is a stopping limit, not a promise that all pilot calls will fit. Interleave conditions so a costly model cannot consume the pilot budget before the others are attempted. The pilot measures compatibility, strict-output success, reasoning-token use, latency, and actual cost; it does not rank models or select policies.

After the pilot, recompute the full-study estimate using observed token counts before seeking a full-study budget. The runner requires an approved phase and cap; a shared durable ledger reserves conservative request charges before dispatch, settles actual charges, and stops on unknown or excessive billing. Unknown charges remain reserved after a crash. Keep a margin below the user cap and reconcile against OpenRouter billing. The local byte-based reservation is deliberately conservative, not a contractual provider token bound.

No GPUs are needed for this API study. Existing GPU.ai/Runpod preferences remain available for future self-hosted work.

## Progress

- [x] Verify current model listings, reasoning controls, endpoint pricing, and local credential presence.
- [x] Preserve model/endpoint snapshots and register the core conditions.
- [x] Implement runner, cost estimator, selection/freeze validation, and paired analysis.
- [x] Check local parsing, billing, leakage boundaries, and freeze integrity with offline tests.
- [ ] Obtain a new pilot budget; run and document the fitting-only pilot.
- [ ] Use measured costs to finalize and approve full-study scope/budget.
- [ ] Evaluate shared policies; write fitting-derived candidates and log every change.
- [ ] Select on validation; freeze all final configurations.
- [ ] Evaluate full audit/test populations and stability diagnostics.
- [ ] Reconcile billing, reproduce metrics, publish findings and update article/paper claims.

## Sources

- [OpenAI's current model guide](https://developers.openai.com/api/docs/guides/latest-model) and [reasoning controls](https://developers.openai.com/api/docs/guides/reasoning).
- [Anthropic's Opus 5.5 announcement](https://www.anthropic.com/claude-opus-5-5).
- OpenRouter: [Astra](https://openrouter.ai/openai/gpt-6-astra), [Opus](https://openrouter.ai/anthropic/claude-opus-5.5), [DeepSeek](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017), [Kimi](https://openrouter.ai/moonshotai/kimi-k3.1-pro).
- OpenRouter [reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), [routing controls](https://openrouter.ai/docs/guides/routing/provider-selection), and [key limits](https://openrouter.ai/docs/api/reference/limits).
