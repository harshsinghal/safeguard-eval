# Community rule handoff: personal insults

**Status:** Working draft; not tested with a model or in production.

## Policy

**Scope:** Posts in the workplace-problems community.

**Remove:** A post that uses a personal insult to attack someone.

**Allow:** Reports about workplace problems, including vague reports. Allow a member to quote an insult a manager said when sharing the incident or asking for help; quoted words alone are not a violation.

**Human review:** If a post appears potentially insulting but the available text does not make clear whether the writer is quoting someone or attacking them, send it for human review rather than automatically removing it or allowing it.

**Do not send for review solely because a report is vague or lacks detail.**

## Boundary examples

| Post | Intended outcome | Reason |
|---|---|---|
| “They said something awful to me.” | Allow | Vague report; no insult by the writer is evident. |
| “My manager called me useless, but he is the idiot.” | Remove | The quote is a report, but “he is the idiot” attacks the manager. |
| “He called me that word again.” | Allow | A report; the text does not itself show an insult or an attack by the writer. |
| “My manager called me useless. What should I do?” | Allow | Quoted insult in a workplace report/help request. |
| “You’re useless.” | Remove | Direct personal insult. |
| “Useless.” (with no clear target or attribution) | Human review | Potential insult; the text does not show whether it is quoted or an attack. |

Examples illustrate intended labels, not measured system performance. The review example assumes the wording is potentially insulting; ambiguity alone without a possible insult is not enough.

## What the policy owner can do

- Confirm that “personal insult” and “attack” capture the intended rule, and decide whether this scope applies to replies, usernames, or other content surfaces.
- Review examples and add sanitized or fictional edge cases, especially quoted language, replies to prior context, and insults without an obvious target.
- Decide who handles review and what action reviewers may take; the draft specifies routing for review, not the final reviewer outcome.
- Check errors after testing: helpful reports wrongly removed or reviewed, and personal attacks that remain allowed.

## What engineering needs to check

- Whether the selected model and interface can preserve the distinction between the policy instructions and the post being judged; verify the full policy and exception survive any model-specific formatting.
- Whether the system supports three outcomes—ALLOW, REMOVE, and REVIEW. A binary model does not become a reliable three-way classifier just because the prompt asks for REVIEW. If review is implemented with a score threshold or separate routing logic, test and document it.
- How missing conversation context, errors, timeouts, and uncertain outputs are handled; do not silently convert REVIEW or failures into REMOVE/ALLOW.
- Evaluate with policy-owner-labelled examples, including all boundary cases above and varied near-misses. Keep model, adapter, and decision settings fixed when comparing policy wording; inspect false removals, missed insults, and review volume.
- Record the policy version, model/version, rendered input, and decision settings. Retest after changing the policy or model before deployment; provide human oversight and a way to revert.

The Safeguard Eval research supports treating policy wording and its model interpreter as a combination to test; it does not validate this community rule or guarantee a deployment outcome.
