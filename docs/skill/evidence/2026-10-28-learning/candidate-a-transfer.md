# Safeguard Eval — Pi conversation review

Run: 20261029T015713Z-38d945. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 24,
    "output": 1742,
    "cacheRead": 54221,
    "cacheWrite": 11508,
    "totalTokens": 67495
  },
  "model_responses": 8,
  "pi_estimated_cost_usd": 0.002854110000000001,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.00285411,
  "billing_records_available": 8,
  "billing_records_requested": 8
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 30776e8d (parent d9d022e7; session.jsonl)

Do I need a specialist policy model, or could I use Qwen? If I get my rule working with Qwen, can our engineers switch to the small PolicyLM model later? What did Safeguard Eval actually find about that direction?

## Assistant · 6281369b (parent 8f442be2; session.jsonl)

**You can start with Qwen; Safeguard Eval did not find that you must use a specialist.** In its WildGuard prompt-harmfulness comparison, selected Qwen3.5 configurations ranged from **83.05% accuracy at 2B** to **91.29% at 27B**. Those are results on one benchmark with model-specific instructions and settings—not predictions for your policy or production deployment. [Study results](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

But getting a rule to work on Qwen **doesn’t establish that the same wording will work on PolicyLM**. The most relevant transfer test went the other way than your proposed move: a policy selected using **Qwen3.5 2B** was then tested on **PolicyLM 1.7B**. On the WildGuard test set, PolicyLM fell from **85.05% to 81.75% accuracy** with that transferred policy. It caught 10 more harmful prompts, but falsely blocked 66 more benign ones—56 more errors overall. Qwen3.5-27B wrote the revisions, but the policy was selected using Qwen 2B; “selected using” and “written by” are not the same. [Transfer matrix](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json)

That **doesn’t directly answer Qwen-to-PolicyLM for your rule**: it’s one bounded experiment on one task, not a test of your policy, and the project’s other transfer examples show that results can depend on the direction. The practical takeaway is to use Qwen to draft and iterate if that suits your workflow, but treat PolicyLM as a **new interpreter to validate**, not a drop-in replacement. Render the rule for its supported input format, then test it on representative examples and inspect both missed violations and false blocks. Safeguard Eval’s broader finding was that policy text, model interface, and decision settings work as a tested combination—not that transfer never works or specialists always win.

## User · 2fb88c01 (parent 6281369b; session.jsonl)

What about the other direction: a policy selected for PolicyLM used with Qwen 2B? Please explain the changed mistakes as well as the accuracy, and show me the source.

## Assistant · 12e7efb2 (parent 48daaa23; session.jsonl)

For the **PolicyLM-selected policy used with Qwen3.5 2B**, accuracy rose slightly on the WildGuard prompt-harmfulness test: **80.11% → 80.87%** across 1,699 prompts.

The mistakes shifted in both directions:

- **False blocks of benign prompts:** 266 → 246 (**20 fewer**)
- **Missed harmful prompts:** 72 → 79 (**7 more**)
- **Total errors:** 338 → 325 (**13 fewer**)

So the policy reduced false blocks, at the cost of missing a few more harmful prompts; the net change was 13 fewer errors. This was a policy **selected using PolicyLM validation feedback**, not written by PolicyLM: Qwen3.5-27B authored the revisions in that search. The comparison held Qwen’s adapter and decision settings fixed.

**Source:** [Safeguard Eval transfer analysis](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json) · [study readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

This was one bounded transfer search on a previously examined test set—not evidence that a PolicyLM-selected policy will improve your Qwen setup.

## User · 567bc0cd (parent 12e7efb2; session.jsonl)

Did a policy tuned for the big Qwen 27B improve PolicyLM? Would that be a good way for us to get the best of both models?

## Assistant · 183f6a0e (parent 4a891fd5; session.jsonl)

**No improvement was observed in that transfer search.** For PolicyLM 1.7B, the policy selected using Qwen3.5 27B was the **unchanged initial policy**. PolicyLM’s accuracy stayed at **85.05%**, with no change in mistakes: **142 false blocks** and **112 missed harmful prompts** across 1,699 WildGuard prompts.

So this particular result does **not** show that a Qwen 27B–selected policy gives PolicyLM “the best of both models.” It shows that, among the candidates in this bounded search, Qwen 27B’s validation procedure selected the starting policy for PolicyLM. A different selection procedure or your own policy could behave differently.

You could use a large model to help draft or review a policy and then test it on both models—but don’t assume a shared policy will optimize both. Measure each model’s false blocks and missed violations separately, and choose based on your application’s priorities. The study tested policy transfer, **not** a combined system that runs both models or merges their decisions.

**Sources:** [transfer analysis](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json) · [study readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

