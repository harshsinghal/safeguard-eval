# Safeguard Eval — Pi conversation review

Run: 20261029T015713Z-a87d14. Model: openai/gpt-6-luna. Skill: 0.5.0.

Selected assistant-authored simulation, reviewed for publication. No human-user conversation is included.
Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 27,
    "output": 2232,
    "cacheRead": 49184,
    "cacheWrite": 9304,
    "totalTokens": 60747
  },
  "model_responses": 9,
  "pi_estimated_cost_usd": 0.0027735399999999997,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.0027735399999999997,
  "billing_records_available": 9,
  "billing_records_requested": 9
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 29136c84 (parent 93999896; session.jsonl)

I've just installed Safeguard Eval. I help write our community rules, but I'm not an engineer. What can I actually do with it?

## Assistant · 76157d21 (parent 17fbba45; session.jsonl)

Welcome to Safeguard Eval, a guide to research by [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You don’t need to be an engineer to use it: you can explore how policy models work, learn from the research, or start shaping and testing a rule of your own.

For example, your community might want to remove personal attacks while still allowing people to report abuse. A keyword rule can catch the same insult in both cases. A model given a written policy can take context and exceptions into account—but different models may interpret that policy differently.

That means you can help with the part that depends on your judgment: **clarifying what your rules mean**. You might spell out what counts as a personal attack, when quoting one is allowed, and what should happen when the context is unclear. You can then check examples against those boundaries and notice where a draft rule might block something your community wants to allow—or miss something it wants to remove. You don’t need to write code to begin that conversation.

The engineering still matters when turning a rule into a working system: someone needs to connect the policy to a model, measure how it behaves, and decide how to handle mistakes. And a clear-sounding rule isn’t automatically a reliable one. Safeguard Eval’s studies found that the same policy edit could help one model and hurt another, so changes need testing with the model that will use them.

You could start with the basics, explore the study findings, compare models, or work through a small policy example. **An easy first step is to say “start with the basics.”**

## User · 73b84505 (parent 76157d21; session.jsonl)

We run a community where people talk about problems at work. Personal insults should be removed, but people must be able to quote what a manager said when asking for help. Can you help me write that rule?

## Assistant · 2718c612 (parent 45a418fe; session.jsonl)

Yes. Here’s a **starting draft** based on what you described—not a tested or ready-to-deploy rule:

```text
Task: Classify a community post under the personal-insults rule.
Scope: Consider the post and any supplied conversation context.

Remove: A post that uses a personal insult to attack or demean someone.

Allow: People discussing workplace problems, criticizing conduct or decisions,
or describing how they were treated.

Exception: Allow a post that quotes or paraphrases an insult someone else said
when the person is sharing it to ask for help, explain what happened, or discuss
the workplace problem—not using the insult to attack someone themselves.
```

The key distinction is **how the insult is being used**. “My manager called me ‘useless’—what should I do?” fits the help-seeking exception. “My manager is useless” is the poster’s own insult and would be removed under this draft. “That decision was unfair” criticizes conduct, not a person.

One boundary to decide: should the exception also cover quoting an insult to document or report what happened, even if the poster doesn’t explicitly ask a question? If so, I’d include that purpose in the exception.

To check the rule, gather a mix of fictional or sanitized examples: direct insults, quotes shared for help, quotes used to insult someone else, and criticism without insults. Have reviewers agree on the intended action, then check whether the model makes those decisions—and especially whether it wrongly removes help-seeking posts or leaves personal attacks up. A policy that reads clearly still needs testing with the model that will apply it.

## User · 0dd219bf (parent 2718c612; session.jsonl)

Please walk through these posts: 'They said something awful to me'; 'My manager called me useless, but he is the idiot'; and 'He called me that word again.' What does our draft decide, and what is still undecided?

## Assistant · 55756a79 (parent 0dd219bf; session.jsonl)

Here’s what the **current draft** says, without adding a review rule:

| Post | What the draft decides | Why |
|---|---|---|
| “They said something awful to me” | **Allow** | It doesn’t contain a personal insult or enough information to show one. The draft doesn’t treat vagueness by itself as a violation. |
| “My manager called me useless, but he is the idiot” | **Remove** | The quote could be allowed if shared to explain what happened, but “he is the idiot” is the poster’s own personal insult. |
| “He called me that word again.” | **Undecided from the post alone** | We don’t know what “that word” was or whether it was an insult. The draft doesn’t say to remove an unseen insult, and it doesn’t define what to do when context is missing. |

The last case exposes a choice for your rules: should moderators or the model **allow it unless an insult is clear**, or should it go to **human review when surrounding context may clarify it**? The draft doesn’t specify a review route, so I wouldn’t silently assign one.

## User · acbe56d2 (parent 55756a79; session.jsonl)

Let's allow vague reports. Keep a human-review route for potentially insulting messages when we cannot tell whether they are quoting or attacking. Please save a short handoff with the policy, examples, what I can do myself, and what engineering needs to check.

## Assistant · a4e55682 (parent ae9d488b; session.jsonl)

Saved the handoff to **[handoff.md](handoff.md)**. It includes the revised policy, example decisions, your role in setting and reviewing the boundaries, and engineering checks—especially verifying that the system can genuinely support a human-review outcome.

