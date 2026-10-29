# Community personal-insults policy — handoff

**Status:** Working draft, based on the community owner's stated boundaries. Not model-tested.

## Policy

**Task:** Classify a community post under the personal-insults rule. Consider the post and any supplied conversation context.

- **REMOVE** a post that uses a personal insult to attack or demean someone.
- **ALLOW** workplace-problem discussions, criticism of conduct or decisions, and reports of how someone was treated. Vague reports are allowed; missing detail alone is not a reason to remove or review.
- **ALLOW** a quote or paraphrase of an insult when it is shared to ask for help, explain what happened, or discuss the workplace problem—not to attack someone.
- **HUMAN REVIEW** a potentially insulting message when the available context does not let you tell whether the poster is quoting/reporting an insult or using it to attack someone. Do not send a message to review merely because it is vague; there must be potentially insulting language and a genuine ambiguity about its use.

## Example decisions

| Post | Intended decision | Reason |
|---|---|---|
| “They said something awful to me” | ALLOW | Vague report; no personal insult is present in the text. |
| “My manager called me useless, but he is the idiot” | REMOVE | The poster uses “idiot” to insult the manager, even though the first insult is quoted. |
| “He called me that word again.” | ALLOW | Vague report with no potentially insulting word shown; missing detail alone does not trigger review. |
| “You’re an idiot.” | REMOVE | Direct personal insult. |
| “My manager called me ‘useless’—what should I do?” | ALLOW | Insult is quoted in a help-seeking report. |
| “He called me ‘useless.’” | HUMAN REVIEW if context does not establish whether this is a report/quote or an attack | Potentially insulting language, but its use is unclear. |

Examples are illustrative; reviewers should apply the rule to the full available context.

## What the policy owner can do

- Decide whether these boundaries reflect the community's intent, especially what counts as a personal insult and what purposes qualify as reporting/help-seeking.
- Review and label representative examples, including near-misses and ambiguous cases, and decide whether the resulting false removals, missed insults, and review workload are acceptable.
- Approve changes to the policy and its examples. Keep policy meaning separate from technical choices about how a model receives it.

## What engineering needs to check

- Confirm the chosen model's native input format and map the policy, context, and labels without dropping the exception or review condition.
- Verify that the system can actually produce **ALLOW / REMOVE / HUMAN REVIEW**. The main Safeguard Eval studies were binary classifications; mentioning REVIEW in policy text does not create a reliable third outcome. If the model is binary, design and evaluate an explicit abstention/review mechanism rather than silently mapping ambiguity to allow or remove.
- Test with the selected model and fixed settings on varied, appropriately reviewed examples. Inspect false removals of reports, missed personal attacks, and review decisions/workload. Keep examples used to revise the policy separate from a held-out test set.
- Version and record the policy, model revision, rendered input, and decision settings together; retest after policy or model changes.

This handoff is a draft and test plan, not evidence that any model implements the policy reliably. Do not use confidential workplace records as examples unless appropriately authorized and protected; fictional or sanitized cases are sufficient to start.
