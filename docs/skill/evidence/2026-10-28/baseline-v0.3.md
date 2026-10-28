# Safeguard Eval — Pi conversation review

Run: 20261028T193710Z-47117c. Model: openai/gpt-6-luna. Skill: 0.3.0.

Local review only. Check for private information before sharing. No automatic upload.
Original visible turns are in append order; IDs preserve branches. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 21,
    "output": 1489,
    "cacheRead": 27387,
    "cacheWrite": 19706,
    "totalTokens": 48603
  },
  "model_responses": 7,
  "pi_estimated_cost_usd": 0.00348372,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.00348372,
  "billing_records_available": 7,
  "billing_records_requested": 7
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 0821d5bd (parent cf0e23bf)

I've installed Safeguard Eval. What is this about? I don't know the model names.

## Assistant · 5d3100ac (parent 2afe53df)

Welcome! Safeguard Eval is a guide to research by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You don’t need to know the model names—or have a technical background—to start.

Imagine a community that wants to stop personal attacks but still let people report abuse. A keyword rule might catch an insult in both cases. A trained classifier can learn from examples, but its decisions depend on what it was trained to recognize.

A **policy model** offers another approach: give a model a written policy—what to allow or block, and any exceptions—and ask it to classify content under that policy. That makes policy text easier to change, but wording, examples, and how the model receives the policy can all affect its decisions. In other words, the policy and the model need to be tested together.

Safeguard Eval studied this with examples involving harmful requests and hate speech. The same policy edit sometimes helped one model and hurt another; some policies transferred between models, while others didn’t. These are results from particular tests, not a universal ranking of models. The practical takeaway is that plain-language rules can shape system behavior, so they deserve careful testing.

Pick a direction—or just say **“start with the basics”**:

1. **Start with the basics:** How did we get from keyword rules to policy models?
2. **Explore the findings:** What changed, and what worked or didn’t?
3. **Compare models and transfer:** Can you use a general-purpose model or reuse a policy?
4. **Try writing a policy:** Work through a small example and how to test it.
5. **Go deeper:** Explore the datasets, model guides, or research paper.

## User · 7ffc8cca (parent 5d3100ac)

Show me a simple example. We want to remove threats but let people report abuse.

## Assistant · 6302d9e6 (parent ae64105b)

Here’s a simple **draft to discuss**, not a tested or deployment-ready rule:

```text
Task: Decide whether a message violates the threats policy.
Use the message and any available conversation context.

BLOCK: The speaker threatens physical harm against a person.
ALLOW: Complaints, criticism, and reports of abuse that do not themselves
       make a threat.
Exception: Allow someone quoting or describing a threat when they are
           reporting it, seeking help, or condemning it.
REVIEW: If it’s unclear who is threatening whom, or what the message means.
```

A few example decisions:

| Message | Intended decision | Why |
|---|---|---|
| “Your service is terrible. I want a refund.” | **ALLOW** | It’s criticism, not a threat. |
| “I’ll come to your office and hurt you.” | **BLOCK** | The speaker threatens physical harm. |
| “Someone told me ‘I’ll hurt you.’ How do I report it?” | **ALLOW** | The person is reporting a threat, not making one. |
| “You’ll regret this.” | **REVIEW** | It could be threatening, but needs context. |

The key distinction is **making a threat versus reporting one**. Before using a rule like this, decide what counts as a threat for your community—for example, whether implied threats or threats toward property are included. Then test it on varied examples, checking both for reports wrongly blocked and threats wrongly allowed. **REVIEW** also needs a real workflow; mentioning it in a policy doesn’t ensure a model can reliably produce that outcome.

## User · 6fa8d28f (parent 6302d9e6)

If I write that policy for PolicyLM, can I use it with Qwen? What did the research actually find?

## Assistant · d46f3d25 (parent 04cb3ffc)

**You can reuse the policy’s meaning, but don’t assume you can use it unchanged or get the same decisions.** PolicyLM and Qwen have different input formats. In the research setup, PolicyLM received separate fields for the rule to block, what to allow, and exceptions. Qwen received a classification instruction and policy in its system message, with the content separately. Your policy would need to be adapted to Qwen’s interface, then tested. Neither approach guarantees a reliable **REVIEW** outcome; that needs its own tested routing.

**What the research found:** In one transfer study, a policy selected for PolicyLM did worse when transferred to Qwen 2B: accuracy fell from **80.11% to 75.10%**. Transferring the other way also hurt: a Shieldstral-selected policy gave PolicyLM **74.57%**, compared with its initial **85.05%**. But transfer wasn’t always harmful: a Qwen-2B-selected policy improved Shieldstral from **87.82% to 90.76%**. So transfer can work, but the direction and recipient matter. These results are from a bounded search on a **harmful-prompt** benchmark—not your threat-reporting policy—so they don’t predict how your policy will perform.

More broadly, policy edits sometimes helped one model and hurt another, and changes in decision cutoffs could also affect results. The practical advice is to adapt the policy to the target model, then test it on examples relevant to your boundary—especially direct threats, reports or quotations of threats, and ambiguous cases. Review both **threats mistakenly allowed** and **legitimate reports mistakenly blocked**.

Sources: [model interfaces](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/evals/run.py), [transfer study](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/policy-transfer/READOUT.md), [study findings](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/published_runs/2026-10-24-wildguard/README.md).

