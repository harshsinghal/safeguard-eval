# Safeguard Eval — Pi conversation review

Run: 20261029T020058Z-5feff0. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 24,
    "output": 2241,
    "cacheRead": 42912,
    "cacheWrite": 9779,
    "totalTokens": 54956
  },
  "model_responses": 8,
  "pi_estimated_cost_usd": 0.002774395,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.002774395,
  "billing_records_available": 8,
  "billing_records_requested": 8
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 889ff64a (parent 0f3b7177; session.jsonl)

I've just installed Safeguard Eval. I help write our community rules, but I'm not an engineer. What can I actually do with it?

## Assistant · 1dca46e3 (parent 44d9e0d0; session.jsonl)

Welcome! Safeguard Eval is a guide to research by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You don’t need to be an engineer to use it.

The practical thing you can do is **turn a community rule into a clear written policy, then think through how a model might apply it**. For example, a keyword filter might catch an insult both when someone is attacking a member and when someone is reporting abuse. A policy can spell out the difference—but the wording, exceptions, and examples can affect the model’s decisions, so they need testing too.

You can contribute the parts that require knowing your community: what behavior is in or out of scope, what exceptions matter, and which mistakes are more serious—removing a harmless post or missing a harmful one. Engineers can handle connecting the policy to a model and measuring its results. Safeguard Eval can help you learn the approach, explore research findings, or work through a policy and a test plan. It doesn’t automatically moderate your community or guarantee a model will follow a rule correctly.

The research found that the same policy edit could help one model and hurt another. So treat a policy and the model interpreting it as a pair to evaluate—not as a rule that will work identically everywhere. [Welcome and guided learning](https://github.com/harshsinghal/safeguard-eval/blob/learning-v0.5-retest/authoring/agent/skills/safeguard-eval/references/start-here.md) · [Research paper](https://github.com/harshsinghal/safeguard-eval/blob/learning-v0.5-retest/authoring/agent/skills/safeguard-eval/references/paper.md)

If you like, we can start with a small example: **a rule that removes personal attacks but allows people to report abuse**.

## User · ee02b80c (parent 1dca46e3; session.jsonl)

We run a community where people talk about problems at work. Personal insults should be removed, but people must be able to quote what a manager said when asking for help. Can you help me write that rule?

## Assistant · 8056115f (parent 6aa3f8e8; session.jsonl)

Yes. Here’s a **draft based on what you’ve said**—it’s a starting point to review, not a tested rule:

> **Personal insults**
>
> Remove content that personally insults or demeans another person in the community.  
> **Allow** people to quote or describe insulting words someone else used when they are sharing a workplace problem or asking for help. A quote is not, by itself, a personal attack by the person posting it.
>
> **Examples**
> - “You’re useless,” directed at another community member → **Remove**: it’s a personal insult.
> - “My manager said, ‘You’re useless,’ and I don’t know how to respond” → **Allow**: the poster is quoting their manager while asking for help.

The key distinction is **who the insult is aimed at and how the poster is using it**: quoting an insult to explain a problem is different from directing one at someone. One choice to settle: should insults aimed at a manager also be removed, or is your rule specifically about insults directed at community members?

## User · e374a8e7 (parent 8056115f; session.jsonl)

Please walk through these posts: 'They said something awful to me'; 'My manager called me useless, but he is the idiot'; and 'He called me that word again.' What does our draft decide, and what is still undecided?

## Assistant · 9a117ff0 (parent e374a8e7; session.jsonl)

Under the current draft:

- **“They said something awful to me” — Allow.** It describes a bad experience but doesn’t itself insult anyone. The draft doesn’t require people to specify or quote the words.
- **“My manager called me useless, but he is the idiot” — Partly clear, partly undecided.** The quote is allowed as an account of what the manager said. The poster’s “he is the idiot” is an insult aimed at the manager. The draft says to remove personal insults directed at someone in the community, but doesn’t settle whether that rule also covers insults aimed at managers or other people outside the community. So the quote exception doesn’t decide that part.
- **“He called me that word again” — Allow.** It reports an insult without using or directing one. The missing word isn’t, by itself, a reason to remove it or send it for review.

The main open choice is whether the removal rule covers insults directed at **any person**, including managers, or only people in the community.

## User · 8ea18a08 (parent 9a117ff0; session.jsonl)

Let's allow vague reports. Keep a human-review route for potentially insulting messages when we cannot tell whether they are quoting or attacking. Please save a short handoff with the policy, examples, what I can do myself, and what engineering needs to check.

## Assistant · 3920e45e (parent 2b422d00; session.jsonl)

Saved the handoff to [`policy-handoff.md`](policy-handoff.md).

It includes the draft policy, decisions for the example posts, the unresolved question about insults aimed at managers, and separate next steps for you and engineering.

