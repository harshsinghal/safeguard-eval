# Safeguard Eval — Pi conversation review

Run: 20261028T194333Z-b10f4e. Model: openai/gpt-6-luna. Skill: 0.4.0.

Local review only. Check for private information before sharing. No automatic upload.
Original visible turns are in append order; IDs preserve branches. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 24,
    "output": 1638,
    "cacheRead": 74543,
    "cacheWrite": 34270,
    "totalTokens": 110475
  },
  "model_responses": 8,
  "pi_estimated_cost_usd": 0.00585058,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.00585058,
  "billing_records_available": 8,
  "billing_records_requested": 8
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · c8539d30 (parent cbd1f11b)

I've installed Safeguard Eval. What is this about? I don't know the model names.

## Assistant · fed76d18 (parent 2da29763)

Welcome to Safeguard Eval, a guide to research by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You don’t need to know the model names—or have a technical background—to get started.

Imagine a community wants to remove personal attacks but still let people report abuse. A keyword rule might catch an insult in both cases. A trained classifier can use examples to recognize more context. Another approach is to give a language model a written policy and ask it to classify each item. Some models are specially trained to interpret policies; others are general-purpose models used for the same task.

The idea is that policy owners can revise the written instructions without retraining the language model. But the wording, examples, exceptions, and way the policy is presented to a model can change its decisions. So the policy and the model interpreting it need to be tested together.

The research tested these ideas on harmful-request and hate-speech benchmarks. It found that the same policy edit could help one model and hurt another, and that reusing a policy with a different model should be tested rather than assumed to work. These are findings from particular experiments, not a universal ranking of models. The paper describes the project as [“Policy as Interface”](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/research-preprint/README.md).

Pick a direction—or just say **“start with the basics”**:

1. **Start with the basics:** How did we get from keyword rules to policy models?
2. **Explore the findings:** What changed, and what worked or didn’t?
3. **Compare models and transfer:** Can different models use the same policy?
4. **Try writing a policy:** Work through a small example and how to test it.
5. **Go deeper:** Explore the datasets, model guides, or research paper.

## User · 7b6b1f59 (parent fed76d18)

Show me a simple example. We want to remove threats but let people report abuse.

## Assistant · ae671aaf (parent 7b6b1f59)

Here’s a simple **untested draft** to show how that policy might be written:

> **Remove a post if it threatens to hurt or kill a person.** This includes direct threats and threats framed as jokes or wishes when they communicate an intention to harm.  
> **Do not remove a post just because it describes, quotes, or reports someone else’s threat.** For example, “They messaged me, ‘I’ll hurt you’” is a report, not a threat by the person posting it. Send unclear cases for human review.

The important distinction is **who is making the threat**: “I’ll hurt you” is different from “Someone told me, ‘I’ll hurt you’.” Context can be messy, so review is useful when it’s unclear whether someone is reporting a threat or making one.

Before using a policy like this, test it on examples from your situation—including quoted threats, sarcasm, vague language, and threats directed at specific people. Check both kinds of mistake: removing legitimate reports, and allowing actual threats. A model’s labels and policy format affect how to run that test.

Want to try a few example posts together and decide how this draft should classify them?

## User · d14ff1a7 (parent ae671aaf)

If I write that policy for PolicyLM, can I use it with Qwen? What did the research actually find?

## Assistant · 34c86e8e (parent eb5c9444)

**You can reuse the policy’s meaning, but don’t assume the same text will work the same way in Qwen.** PolicyLM and Qwen take policy instructions differently, so you may need to adapt how the policy is packaged—and then test Qwen’s decisions.

The closest direct research comparison was on **WildGuard prompt harmfulness**, not your threats-and-abuse-reporting rule. For the PolicyLM-selected policy tested with **Qwen3.5-2B**, accuracy was **80.9%**, versus **80.1%** for Qwen’s starting policy. With **Qwen3.5-4B**, it was **84.9%**, versus **85.6%** for its starting policy. So transfer was slightly helpful in one tested case and slightly harmful in the other. These benchmark scores don’t tell us whether your specific reporting exception will transfer correctly.

The broader results also showed transfer can go either way: a Shieldstral-selected policy lowered Qwen-2B accuracy from 80.1% to 75.1%, while a Qwen-2B-selected policy improved Shieldstral from 87.8% to 90.8%. The practical lesson is to test the policy with the **exact Qwen model and setup** you plan to use, and inspect both kinds of error: threats that slip through and legitimate reports that get removed.

[Transfer study results](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/published_runs/2026-10-25-policy-transfer/README.md) · [How the model interfaces differ](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/research-directions/POLICY-INTERFACE-AUDIT.md)

