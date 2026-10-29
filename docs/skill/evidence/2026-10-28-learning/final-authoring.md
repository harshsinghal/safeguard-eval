# Safeguard Eval — Pi conversation review

Run: 20261029T020428Z-b2397b. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 33,
    "output": 2854,
    "cacheRead": 153078,
    "cacheWrite": 23284,
    "totalTokens": 179249
  },
  "model_responses": 11,
  "pi_estimated_cost_usd": 0.00587158,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.00587158,
  "billing_records_available": 11,
  "billing_records_requested": 11
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 85bbb7f1 (parent 27407fca; session.jsonl)

I've just installed Safeguard Eval. I help write our community rules, but I'm not an engineer. What can I actually do with it?

## Assistant · 9f8d9476 (parent d9450a19; session.jsonl)

Welcome! Safeguard Eval is a guide to research by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). **You don’t need to be an engineer to use it.** You can work on the part that’s yours: making the community rules clear and deciding where the boundaries should be.

For example, a keyword filter might catch an insult both when someone uses it to attack a member and when someone quotes it to report abuse. A policy model can be given written rules to help make that distinction. You can use this guide to:

- **Draft or clarify a rule**, including what it covers and what exceptions matter.
- **Think through tricky examples**—what should stay up, come down, or be checked by a person?
- **Plan a simple test** of the rule, looking for both unfair removals and violations the system misses.
- **Explore the research** on how models interpret policies and what can change their decisions.

The important catch is that clearer wording doesn’t guarantee consistent results: different models may interpret the same policy differently, and edits can help one model while hurting another. So treat a draft as something to test, not a promise about how a live system will behave. Engineers may still be needed to connect a model to your platform, run evaluations, and deploy it—but you can help define what the rules should mean.

The research’s [overview](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/research-preprint/README.md) and [HateXplain study readout](https://github.com/harshsinghal/safeguard-eval/blob/e08554bf6af217e5e34820986f02c23a845b4f6d/docs/hatexplain/READOUT.md) are available if you’d like to explore further.

**Start with the basics**, or tell me one community rule you’re working on and we can make a first draft together.

## User · 8369eaa1 (parent 9f8d9476; session.jsonl)

We run a community where people talk about problems at work. Personal insults should be removed, but people must be able to quote what a manager said when asking for help. Can you help me write that rule?

## Assistant · 9e55064c (parent d6175477; session.jsonl)

Yes. Here’s a **first draft** based on what you’ve said:

> **Personal insults:** Remove messages that use a personal insult to attack someone.  
> **Workplace-help exception:** Allow a member to quote an insult a manager said when sharing it to ask for help. The quoted words alone are not a reason to remove the post.

The key distinction is **whether the writer is insulting someone or reporting what someone else said**. For example:

| Example | Intended action | Why |
|---|---|---|
| “My manager called me ‘useless.’ What should I do?” | Allow | The member is quoting the manager while asking for help. |
| “My manager is useless.” | Remove | The member is directing a personal insult at the manager. |

One boundary is still open: **Should members also be allowed to quote insults when they’re discussing the incident but not explicitly asking for help?** I haven’t included that broader exception in the draft.

This is a policy draft, not a guarantee that a model will apply it correctly. Before using it, test it on varied examples—including reports, direct insults, and borderline cases—and check both for helpful posts wrongly removed and insults that stay up. Safeguard Eval’s walkthrough explains this kind of policy drafting and testing; its examples are illustrative, not evaluated rules for your community.

## User · 20eac4ea (parent 9e55064c; session.jsonl)

Please walk through these posts: 'They said something awful to me'; 'My manager called me useless, but he is the idiot'; and 'He called me that word again.' What does our draft decide, and what is still undecided?

## Assistant · 1fc19711 (parent 20eac4ea; session.jsonl)

Under the draft **as written**:

- **“They said something awful to me” — Don’t remove under this rule.** It contains no personal insult. The draft doesn’t require people to explain what happened.
- **“My manager called me useless, but he is the idiot” — Remove.** The quoted “useless” is allowed as a report, but “he is the idiot” is a personal insult aimed at the manager.
- **“He called me that word again.” — Don’t remove based on this text alone.** It reports something hurtful, but doesn’t show the word or insult anyone in the post. The draft doesn’t say to remove a post just because a referenced word might have been insulting.

**Still undecided:** whether quoting an insult is allowed when the member isn’t explicitly asking for help. The third post may raise that question, but its wording alone doesn’t establish that it contains an insult or should be removed.

## User · b9d2d9f3 (parent 1fc19711; session.jsonl)

Let's allow vague reports. Keep a human-review route for potentially insulting messages when we cannot tell whether they are quoting or attacking. Please save a short handoff with the policy, examples, what I can do myself, and what engineering needs to check.

## Assistant · c9f678fc (parent 8cc17d22; session.jsonl)

Saved the handoff to **`policy-handoff.md`**. It includes the revised rule, example decisions, the human-review boundary, and separate next steps for you and engineering.

I kept vague reports allowed, and review limited to potentially insulting posts where the text leaves quoting versus attacking unclear. The policy and examples are a working draft, not a tested model configuration.

