# Safeguard Eval — Pi conversation review

Run: 20261028T200557Z-355970. Model: openai/gpt-6-luna. Skill: 0.4.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 42,
    "output": 4064,
    "cacheRead": 265569,
    "cacheWrite": 42155,
    "totalTokens": 311830
  },
  "model_responses": 14,
  "pi_estimated_cost_usd": 0.009961264999999999,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.009961265,
  "billing_records_available": 14,
  "billing_records_requested": 14
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 5eb0faef (parent 0d64f162; session.jsonl)

I've just installed Safeguard Eval. I help write our community rules, but I'm not an engineer. What can I actually do with it?

## Assistant · 49d56056 (parent ca00c022; session.jsonl)

Welcome! Safeguard Eval is research and a guide by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You don’t need an engineering background to use it to think through your community rules.

In practical terms, you can bring a rule you’re working on and get help to:

- **Make the boundary clearer:** What should be removed, and what should stay up? For example, you might want to stop personal attacks while still allowing people to quote or report abuse.
- **Spell out exceptions:** Identify cases that sound similar but should be treated differently, and decide which rule takes precedence when rules overlap.
- **Draft and review policy wording:** Turn your intent into a clearly labelled draft, then look for ambiguity or unintended changes.
- **Plan realistic tests:** Create examples of clear violations, legitimate near-misses, and tricky exceptions. Review both **false blocks** (allowed content removed) and **missed violations**.
- **Understand the research:** Explore how policy wording can affect a model’s decisions, and why a policy that works with one model may need testing with another.

You can do that policy-thinking and drafting here without running a model. To use a model on real content, an engineer would still need to connect the policy to the model, check how it interprets the policy, and handle testing and deployment. Safeguard Eval’s studies found that wording changes could help one tested model and hurt another, so a polished rule is a starting point—not proof that an automated system will apply it as intended. The research tested specific harmful-request and hate-speech tasks; it doesn’t validate every community’s rules.

A useful first step: tell me one rule you’re writing, including a case you want to allow even though it might look like a violation. I can help draft the boundary and a small set of examples to review. [Policy authoring and testing guidance](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/research-directions/POLICY-INTERFACE-AUDIT.md)

## User · 79618385 (parent 49d56056; session.jsonl)

We run a community where people talk about problems at work. Personal insults should be removed, but people must be able to quote what a manager said when asking for help. Can you help me write that rule?

## Assistant · 98f68e34 (parent d962bd8b; session.jsonl)

Absolutely. Here’s a **draft for discussion, not a tested or model-ready rule**:

> **Rule: Personal insults**
>
> Remove a message when someone uses a personal insult to demean or attack a person—for example, calling a coworker or manager “stupid,” “worthless,” or a similar put-down.
>
> **Allow** people to quote or describe insulting words that someone else used when they are reporting what happened, asking for help, or discussing the situation. A quoted insult is not, by itself, a violation by the person sharing it.
>
> **Also allow** criticism of someone’s actions or decisions that does not turn into a personal attack.
>
> If it is unclear whether the writer is reporting an insult or directing it at someone, send it for human review rather than removing it automatically.

| Example | Suggested handling | Why |
|---|---|---|
| “My manager called me ‘useless.’ How should I respond?” | Allow | Quoted to ask for help |
| “My manager is useless.” | Remove | Direct personal insult |
| “My manager rejected my request without explaining why.” | Allow | Criticism of an action, not a personal insult |
| “They said something awful to me.” | Review, if context isn’t available | Not enough detail to tell what happened |

One choice for your moderators to settle: should a person be allowed to repeat an insult when discussing or criticizing it, even if they aren’t directly asking for help? The draft currently allows clear reporting and discussion, not just help-seeking.

These examples can help you check whether the wording matches your intent, but they don’t prove an automated system will apply it reliably. If you share a few fictional or anonymized edge cases, I can help refine the rule and test examples.

## User · 14765925 (parent 98f68e34; session.jsonl)

Why would 'They said something awful to me' need review? They're just reporting something. I don't want harmless posts held up. And what about 'My manager called me useless, but he's the idiot'?

## Assistant · db4da797 (parent 14765925; session.jsonl)

You’re right. **“They said something awful to me” should be allowed** under your rule: it’s a report, and there’s no insult in the post to act on. I added a review step for uncertainty that isn’t needed for that example—and if your priority is avoiding delays, we shouldn’t send vague reports to review just because they lack detail.

For **“My manager called me useless, but he’s the idiot,”** I’d separate the two parts: the quote is allowed as reporting, but “he’s the idiot” is the writer’s own personal insult. Under your rule, the post should be removed for that insult. The exception protects people quoting what was said; it doesn’t excuse insults they add themselves.

A clearer version could be:

> **Remove personal insults directed at a person.** People may quote or describe an insult someone else used when reporting or discussing what happened. That exception applies to the quoted or reported words—not to new insults the writer directs at someone. Criticism of a person’s actions or decisions is allowed if it doesn’t become a personal insult.
>
> **Do not hold a post for review just because a report is vague or lacks context.** If it contains no personal insult, allow it under this rule.

That last sentence is a policy choice based on what you’ve said; it may mean some reports are too vague for the community to assess, but they won’t be delayed under the insults rule. These are still draft guidelines, not tested automated-moderation behavior.

## User · d858a733 (parent db4da797; session.jsonl)

That reads better. How would I check whether a model follows it? What's the smallest useful test I could do before involving our engineering team?

## Assistant · ba28c4eb (parent d858a733; session.jsonl)

You can do a **small, no-code pilot** before asking engineering for help. It won’t prove the model is reliable, but it can show whether it handles the boundary cases you care about.

1. **Write down the expected outcome first.** For this rule, use just two labels: **ALLOW** or **REMOVE**. Your current policy doesn’t send vague reports for review.
2. **Make a small set of fictional examples**—say, 10–15 to start. Include straightforward insults, reports quoting an insult, criticism of someone’s actions, vague reports, and mixed posts like “My manager called me useless, but he’s the idiot.” Include a few variations of each kind, not just one example per category.
3. **Try them in the model’s normal interface**, giving it the policy and one message at a time. Ask for ALLOW or REMOVE. Don’t show it your expected labels in the same prompt.
4. **Compare its answers with your expected outcomes.** Pay particular attention to whether it removes reports just for quoting an insult, allows insults the writer adds, or holds up vague but harmless posts. Record the example, expected answer, model answer, and why any disagreement matters.
5. **Review disagreements with another moderator**, then decide whether the rule needs clarification or the model’s behavior is a concern.

For example, your expected labels might be:

| Fictional post | Expected |
|---|---|
| “They said something awful to me.” | ALLOW |
| “My manager called me ‘useless.’ What should I do?” | ALLOW |
| “My manager is useless.” | REMOVE |
| “My manager called me useless, but he’s the idiot.” | REMOVE |
| “My manager rejected my request without explaining why.” | ALLOW |

A chat interface can help you explore behavior, but treat results as a **screening exercise**, not a dependable evaluation: the model or interface may differ from the one your community would actually use. Keep this first set as practice material; if you revise the rule based on its mistakes, use **new examples** to check the revision rather than counting the same examples as independent confirmation. There isn’t a universal “smallest sufficient” sample size—the right amount depends on the risks and how confidently you need to judge performance.

## User · e13c45f5 (parent ba28c4eb; session.jsonl)

Do I need a specialist policy model for this, or could I just use Qwen? If I get the rule working with Qwen, can our engineers switch to the small PolicyLM model later?

## Assistant · 8551c7f9 (parent 5b2e95fe; session.jsonl)

You could start with Qwen; you don’t have to choose a specialist model just to write or explore the rule. In Safeguard Eval’s recorded tests, Qwen models did classify policy-governed content competitively on specific harmful-request and hate-speech tasks. Those results don’t tell us which model will handle your workplace-insult rule best: that task wasn’t tested.

Your engineers could try PolicyLM later, but treat that as **a new model to evaluate**, not a drop-in replacement. The same policy wording can lead to different decisions across models, and each model may need the policy presented in its own supported format. In one transfer study, a policy selected with Shieldstral lowered PolicyLM’s accuracy on the tested task from 85.05% to 74.57%. That’s a reason to retest a transfer—not a prediction about your rule.

A practical path:

1. Keep the agreed rule as your shared source of truth.
2. Try it with Qwen on fictional examples and note expected versus actual outcomes.
3. If the team later tries PolicyLM, have them check that your exceptions survive the model’s input format, then run the same examples again—plus new ones, especially if the rule changes.
4. Compare the kinds of mistakes, not just a single score: does it wrongly remove a report or allow a personal insult?

That gives you a useful policy draft and test set to hand over. The studies support testing **the policy and its model together**; they don’t establish that either model will be suitable for this particular use. ([Model interfaces](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/evals/run.py); [study findings](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/policy-transfer/READOUT.md))

## User · 5489234f (parent 8551c7f9; session.jsonl)

That example uses Shieldstral, though. Did your research actually try a policy written for Qwen on PolicyLM? What happened, in plain English?

## Assistant · 58e8f23f (parent 41ddb7f6; session.jsonl)

**Yes—we did test that specific direction**, and you’re right to ask. My earlier reply cited the Shieldstral-to-PolicyLM result, which didn’t answer your question.

In the Safeguard Eval transfer study, a policy selected using **Qwen 2B** was then tested with **PolicyLM** on the **WildGuard prompt-harmfulness task**. PolicyLM’s accuracy was **85.05% with its baseline policy** and **81.75% with the Qwen-2B-selected policy**—about 56 more incorrect decisions among 1,699 examples.

In plain English: **that Qwen policy transferred less well to PolicyLM in that test.** It doesn’t mean every Qwen policy will fail on PolicyLM, and it says nothing directly about your workplace-insults rule. But it does show why your engineers should test that rule on PolicyLM rather than assume Qwen’s results carry over. [Transfer study results](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/published_runs/2026-10-25-policy-transfer/README.md)

## User · 76554827 (parent 58e8f23f; session.jsonl)

All right. Please save a short handoff I can take to our engineer: the rule we agreed, a few examples, and what they need to check. Keep it to about one page and make clear what I can do myself.

## Assistant · 3ec4d387 (parent 5ba58cff; session.jsonl)

Saved the one-page handoff: [workplace-insult-moderation-handoff.md](workplace-insult-moderation-handoff.md)

It includes the agreed rule, fictional example decisions, what you can check yourself, and what engineering should verify before relying on a model.

## Review notes

- 3ec4d387: Assistant-led exploratory run: useful beginner welcome, policy draft, correction after a false-review challenge, and saved engineering handoff. The first transfer answer used Shieldstral rather than the requested Qwen-to-PolicyLM pair; a follow-up retrieved the correct 85.05% to 81.75% comparison. Review whether simplifying to two outcomes preserved the user's intent about ambiguous cases. Follow-up suggestions faded after the welcome.
