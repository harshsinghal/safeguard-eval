# Safeguard Eval — Pi conversation review

Run: 20261029T020428Z-41c444. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 24,
    "output": 1893,
    "cacheRead": 185397,
    "cacheWrite": 37829,
    "totalTokens": 225143
  },
  "model_responses": 8,
  "pi_estimated_cost_usd": 0.007531494999999999,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.007531495,
  "billing_records_available": 8,
  "billing_records_requested": 8
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 728a01a9 (parent 22760ae3; session.jsonl)

Do I need a specialist policy model, or could I use Qwen? If I get my rule working with Qwen, can our engineers switch to the small PolicyLM model later? What did Safeguard Eval actually find about that direction?

## Assistant · 4bb20c2f (parent e324f012; session.jsonl)

**You don’t have to start with a specialist.** Safeguard Eval got competitive prompt-harmfulness results using Qwen3.5 with a policy: on the WildGuard test, selected configurations ranged from **83.05% accuracy for Qwen3.5-2B to 91.29% for Qwen3.5-27B**. That shows Qwen can be a reasonable place to prototype; it doesn’t establish that every Qwen size or policy will work equally well.

**But getting a rule working on Qwen does not guarantee it will carry over to PolicyLM.** In the project’s specific transfer test, a policy selected using **Qwen3.5-2B** was then evaluated on **PolicyLM 1.7B**. On the same 1,699 WildGuard prompts, PolicyLM’s accuracy went from **85.05% with its initial policy to 81.75% with the Qwen-selected policy**. It falsely blocked 66 more benign prompts, while missing 10 fewer harmful ones. That’s a concrete case where transfer changed the trade-off and made overall accuracy worse—not evidence that your rule will necessarily behave the same way.

So: **prototype in Qwen if it suits your needs, but treat a later switch to PolicyLM as a new tested configuration.** Keep the intended rule’s meaning fixed, adapt it to PolicyLM’s input format, then evaluate both models on representative examples and compare false blocks and missed violations—not just an aggregate score. The experiments used different model-specific interfaces, and the transfer result was one bounded search on a previously examined test set, not a guarantee about a new policy.

Sources: [Qwen results](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-qwen/README.md) · [Exact Qwen-2B → PolicyLM transfer comparison](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

## User · 68b53e09 (parent 4bb20c2f; session.jsonl)

What about the other direction: a policy selected for PolicyLM used with Qwen 2B? Please explain the changed mistakes as well as the accuracy, and show me the source.

## Assistant · 4e97c1c9 (parent 94faa757; session.jsonl)

**For this direction—PolicyLM-selected policy → Qwen3.5-2B—the result improved accuracy slightly, but changed which mistakes Qwen made.**

On the 1,699-prompt WildGuard test, Qwen’s accuracy rose from **80.11%** with its initial policy to **80.87%** with the policy selected using PolicyLM: a gain of **0.77 percentage points**. Qwen made **20 fewer false blocks** of benign prompts, but **missed 7 more harmful prompts**. Overall, that was 13 fewer incorrect decisions.

This comparison used the recipient’s fixed Qwen adapter and decision settings. The policy was selected using PolicyLM’s validation results; it was **not** selected by seeing which policy scored best on Qwen’s test results. Also, Qwen3.5-27B wrote the policy revisions in this study, so “PolicyLM-selected” doesn’t mean “written by PolicyLM.”

**Source:** [Safeguard Eval’s policy-transfer readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md) · [Full transfer results matrix](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json)

This is one bounded comparison on a previously examined test set, not evidence that a particular policy will transfer well in your deployment.

## User · 918bbd4e (parent 4e97c1c9; session.jsonl)

Did a policy tuned for the big Qwen 27B improve PolicyLM? Would that be a good way for us to get the best of both models?

## Assistant · 99278fa2 (parent 5469e2c3; session.jsonl)

**No—not in the recorded transfer search.** Qwen3.5-27B’s validation process selected the **unchanged starting policy**. Applied to PolicyLM 1.7B, it produced exactly the same WildGuard test results as PolicyLM’s initial policy: **85.05% accuracy**, **142 false blocks**, and **112 missed harmful prompts**. There was no improvement from transferring a Qwen-27B-selected revision.

That doesn’t test the full “best of both models” idea. It tests **one model selecting a policy for another model**; it is not an ensemble combining their predictions. The result suggests Qwen-27B’s search found no revision worth selecting for Qwen-27B—not that a jointly designed or separately tested policy could never help PolicyLM.

For your team, treat a policy as portable *candidate text*, not a guaranteed portable behavior: preserve the rule’s intent, render it for each model’s interface, then compare both models on your own representative cases, including false blocks and missed violations. **Don’t assume the policy that works best on the larger Qwen will improve PolicyLM.**

**Sources:** [Full transfer results matrix](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/analysis.json) · [Transfer study readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md)

