# Safeguard Eval — Pi conversation review

Run: 20261029T020058Z-1c7a66. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 24,
    "output": 1875,
    "cacheRead": 54476,
    "cacheWrite": 11645,
    "totalTokens": 68020
  },
  "model_responses": 8,
  "pi_estimated_cost_usd": 0.002940285,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.002940285,
  "billing_records_available": 8,
  "billing_records_requested": 8
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · e19b710d (parent 8f27fa71; session.jsonl)

Do I need a specialist policy model, or could I use Qwen? If I get my rule working with Qwen, can our engineers switch to the small PolicyLM model later? What did Safeguard Eval actually find about that direction?

## Assistant · 0ef42cae (parent 32f6f69d; session.jsonl)

You can prototype the rule with Qwen; you don’t have to start with a specialist. But treat a Qwen-tested rule as a **draft for PolicyLM**, not a drop-in: the policy, model adapter, and decision threshold need testing together.

Safeguard Eval tested the direction you asked about: **a policy selected using Qwen3.5 2B, then classified by PolicyLM 1.7B** on WildGuard prompt-harmfulness. Accuracy fell from **85.05%** with PolicyLM’s initial policy to **81.75%** with the Qwen-selected policy. It also falsely blocked 66 more benign prompts, while missing 10 fewer harmful ones. So the transfer changed the error trade-off, and performed worse overall in that comparison. [Transfer results](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json)

That’s evidence against assuming the rule will transfer unchanged—not proof that your rule can’t. It’s one bounded study on a previously examined test set, not a test of your policy or every Qwen size. The practical path is to draft with Qwen, then render and evaluate the rule with PolicyLM’s native interface, checking false blocks and missed violations before switching. Safeguard Eval’s broader takeaway was that **policy text and the model interpreting it are a tested combination**. [Study summary](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

## User · 689013d8 (parent 0ef42cae; session.jsonl)

What about the other direction: a policy selected for PolicyLM used with Qwen 2B? Please explain the changed mistakes as well as the accuracy, and show me the source.

## Assistant · c329a034 (parent d5967a81; session.jsonl)

For **PolicyLM 1.7B → Qwen3.5 2B**—meaning the policy was selected using PolicyLM, then evaluated by Qwen—the transferred policy modestly improved accuracy on WildGuard prompt-harmfulness:

| Qwen 2B configuration | Accuracy | False blocks | Missed harmful prompts |
|---|---:|---:|---:|
| Qwen’s initial policy | 80.11% | 266 | 72 |
| PolicyLM-selected policy | 80.87% | 246 | 79 |
| Change | **+0.77 percentage points** | **20 fewer** | **7 more** |

So the accuracy gain came with a trade-off: Qwen falsely blocked fewer benign prompts, but missed more harmful ones. Overall, there were 13 fewer incorrect decisions on the 1,699 test prompts.

**Source:** [Safeguard Eval’s transfer analysis](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json) · [study readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

This is a result from one bounded search on a previously examined test set—not a guarantee that a PolicyLM-authored policy will improve your Qwen setup. The policy was selected on PolicyLM, not chosen using Qwen’s results.

## User · dd4c160d (parent c329a034; session.jsonl)

Did a policy tuned for the big Qwen 27B improve PolicyLM? Would that be a good way for us to get the best of both models?

## Assistant · 7f8ef691 (parent 4cd7f9f1; session.jsonl)

No—not in the recorded comparison. For **Qwen3.5 27B → PolicyLM 1.7B**, the policy selected using Qwen 27B was the **unchanged initial policy**. On PolicyLM, it produced exactly the same result as PolicyLM’s initial policy on WildGuard prompt-harmfulness: **85.05% accuracy, 142 false blocks, and 112 missed harmful prompts**. There was no improvement or change in mistakes. [Transfer analysis](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json) · [Readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

So this result does **not** show that a Qwen 27B-tuned policy gets you the best of both models. It shows only that, in this bounded search, Qwen 27B’s validation procedure preferred the starting policy—and that policy did not change PolicyLM’s result. The study did not establish a universally best policy shared across models.

If by “best of both” you mean combining their classifications rather than transferring policy text, that’s a separate approach. Safeguard Eval tested some score ensembles, but those results are configuration- and task-specific; they are not evidence that combining Qwen 27B and PolicyLM would work well for your use case. For your setup, compare each model and any combined approach on the same representative examples, inspecting false blocks and missed violations—not just accuracy.

