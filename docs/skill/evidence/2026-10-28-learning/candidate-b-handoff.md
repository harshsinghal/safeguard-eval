# Community policy handoff: workplace-problem discussions

**Status:** Draft for review; not tested in a model.

## Policy

- Remove personal insults directed at another person **when the post is an attack rather than a report or quotation**.
- Allow members to quote or describe insulting words someone else used when sharing a workplace problem or asking for help. Quoted insulting words alone are not a violation.
- Allow vague reports of a bad or insulting experience. A report does not need to include the exact words.
- Send a potentially insulting message for **human review** when the available text does not make clear whether the poster is quoting/reporting someone else's words or attacking someone. Do not send a post to review solely because context or details are missing.

## Examples and current decisions

| Post | Decision | Why |
|---|---|---|
| “They said something awful to me” | Allow | Vague report; no personal insult by the poster is evident. |
| “My manager called me useless, but he is the idiot” | Allow the quotation; scope of “he is the idiot” is unresolved | The quote is a report. The poster also insults the manager, but it is not yet decided whether the removal rule covers insults aimed at managers or only people in the community. |
| “He called me that word again.” | Allow | Reports an insult without repeating or directing one. Missing the exact word is not a reason to remove or review. |
| “You’re useless” directed at another community member | Remove | Direct personal insult, not presented as a quote or report. |

## Open policy decision

Decide whether direct personal insults aimed at **any person** (including managers) should be removed, or whether the rule applies only to people in the community. Until decided, do not treat the manager-directed insult in the second example as a settled policy outcome. The review route applies to ambiguity about quoting/reporting versus attacking; it does not resolve this separate scope question.

## What the policy owner can do

- Confirm the scope of who is protected by the removal rule, including the open manager question.
- Review examples and decide which errors matter most: removing a legitimate report, missing a personal attack, or sending an unclear case to review.
- Add representative examples, especially paired cases where the same insulting words are quoted in a report versus directed as an attack.
- Approve policy wording and any later changes to its meaning or exceptions.

## What engineering needs to check

- Confirm the chosen model and its native input format support the intended policy text and the three outcomes: **allow, remove, human review**. The research does not validate this three-way workflow automatically.
- Ensure the adapter preserves the reporting exception, vague-report allowance, and review condition; do not silently drop unsupported clauses. Keep policy instructions separate from the post being judged.
- Define how model outputs map to actions, including what happens on errors or uncertain outputs, and verify review cases reach a human.
- Test a labelled set containing clear attacks, quoted/attributed insults, vague reports, and genuinely ambiguous cases. Inspect false removals, missed attacks, and unnecessary reviews—not just one aggregate score.
- Record the exact policy, model/version, adapter, and decision settings used for testing. Retest after changes; policy wording and model behavior need to be evaluated together.
