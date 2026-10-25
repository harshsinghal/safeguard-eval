# Frontier models can classify policies—but the API is part of the experiment

We completed the first pilot with four frontier models through OpenRouter: GPT-6 Astra, Claude Opus 5.5, DeepSeek V4.1 Flash, and Kimi K3.1 Pro. Each model saw the same 32 training prompts twice, once with lower reasoning and once with higher reasoning. That produced **256 planned observations**, plus one rejected provider-routing attempt that we also kept.

The pilot cost **$0.55**, bringing the project's cumulative experimental spend to **$8.46**. Your new cumulative limit is **$20**. Billing has been reconciled against the account's usage increase; no GPU was rented.

This was a compatibility and cost check. We used the original p0 policy throughout. **We have not tuned a new policy, selected a winning prompt, or run the frontier models on WildGuardTest yet.**

The supplied WildGuardTrain labels are model-generated. The separate human-labeled official test set was not used in this pilot.

## What happened when we asked for a label?

The task sounds simple: read a request and return A for ALLOW or B for BLOCK. An API can still fail to produce that label.

| Model | Lower-reasoning valid labels | Higher-reasoning valid labels | What interrupted classification? |
|---|---:|---:|---|
| GPT-6 Astra | 32/32 | 32/32 | None |
| Claude Opus 5.5 | 30/32 | 30/32 | Two content-filtered responses in each setting |
| DeepSeek V4.1 Flash | 32/32 | 31/32 | One upstream rate-limit error in the higher setting |
| Kimi K3.1 Pro | 30/32 | 32/32 | Two answers in the lower setting did not follow the one-letter format |

**A valid label is not necessarily a correct label.** This table measures whether the deployed API completed the classification contract. The small fitting-sample accuracy counts are available in the evidence bundle, but they are not a leaderboard or a held-out estimate.

The content filters are an important practical finding. A moderation workflow must inspect material that may be unsafe. A general-purpose API may filter the request before it delivers a classification. We counted those responses as errors; we did not turn a refusal into BLOCK or change the request to get around the filter. We cannot attribute every API failure to the model's underlying weights.

## Did more thinking help?

It increased reported reasoning-token use, but it did not produce a uniform improvement in this small sample.

Astra returned the same labels at both settings, and Opus had the same outcomes at both settings. Kimi's higher-reasoning condition produced three additional correct outcomes: two came from resolving invalid-output failures and one from a changed label. DeepSeek's higher condition had two fewer correct outcomes, one involving the rate limit. These observations are too small and confounded by service failures to establish a reasoning benefit or a model ranking.

Higher reasoning was also slower. Average request times increased from **1.82 to 2.42 seconds** for Astra, **2.10 to 2.78 seconds** for Opus, **0.83 to 1.47 seconds** for DeepSeek, and **3.22 to 4.44 seconds** for Kimi. These are pilot measurements from sequential calls, including failures—not controlled hardware benchmarks.

For Astra and Opus, the comparison was **low versus high** because their APIs require reasoning. For DeepSeek and Kimi it was **off versus high**. Both off conditions reported zero reasoning tokens. A low setting can also use zero reasoning on an easy request; that does not make it an off setting.

## Why was it cheaper than expected?

The initial estimates allowed for hundreds or thousands of output tokens per request. The models generally used much less on these examples. Some requests also received automatic input-cache discounts. We retained the initial estimates so the difference between an estimate and a measurement is visible.

Scaling the observed average cost to the full registered process gives about **$251** for up to 116,808 requests. That is a planning estimate, not a quote: these 32 prompts may not represent harder examples, new policies may be longer, and caching and provider prices can change.

The full process repeats five policy candidates across fitting and validation data, then evaluates the initial, shared, and selected policies under both reasoning settings on the complete audit and test populations. That repetition—not just one pass over the test set—is why the larger experiment still exceeds the **$11.54** left under the current cumulative cap.

## What comes next?

The pilot has established a working deployment and exposed failure modes we must preserve in the final analysis. The next scientific phase is the planned policy search: edit from fitting errors, select on validation, freeze the chosen prompts, then evaluate all 1,699 labeled WildGuardTest requests. That full phase remains unrun because it does not fit the approved budget.

The [public evidence and reproduction instructions](../../published_runs/2026-10-25-frontier-pilot/README.md) include every attempted observation, costs, source versions, and the provider amendment. The [lab notebook](NOTES.md) records the changes and failed attempts for later articles and research writing.
