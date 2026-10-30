# Do decision-model scores work better together?

**The combination helped a little, but this experiment did not establish a clear
improvement over Jev or outperform WildGuard.** We combined the saved scores from
Jev, Kev, and Clef on WildGuard's harmful-prompt task. The primary ensemble reached
89.32% balanced accuracy, compared with 88.69% for the validation-selected Jev
individual and 89.81% for the released WildGuard model.

That is a useful result even though it is not a new best score. The combination
caught more harmful requests than Jev, but also blocked more benign requests.
It gives us another example of why the decision rule and the types of mistakes
matter alongside the headline number.

## We already had scores, not just decisions

The earlier decision-model studies saved each model's native probability for
BLOCK. We did not ask a chat model to invent a confidence rating. These are the
scores returned by the classification interfaces; they are not proven estimates
of real-world risk.

For each prompt, the ensemble receives three numbers:

```text
Jev BLOCK score ───┐
Kev BLOCK score ───┼── learned combination ── ensemble score ── fixed cutoff ── ALLOW/BLOCK
Clef BLOCK score ──┘
```

No new inference was needed. We reused the archived scores, keeping the underlying
models and policy wording fixed. We trained small classifiers to combine them.
Added GPU/API cost was **$0**.

## How we kept fitting and evaluation separate

We reused 1,024 WildGuardTrain examples to fit the combinations and 512 other
WildGuardTrain examples for validation. Validation chose the policies from the
available pool, the combiner settings, and the final BLOCK cutoff. All those
choices were frozen before this extension loaded scores for the 1,699 labeled
WildGuardTest prompts.

This tests **prompt harmfulness only**. It does not assess response safety or
refusal behavior. The fitting and validation labels are model-generated; the
official test labels are human annotations. The test had also appeared in our
earlier studies. It was held out of this combiner's fitting and selection, but
this is an exploratory follow-up, not a new blind evaluation.

The brief and detailed policies had saved scores for all three splits. The
example-bearing policies had no fitting scores, so they could not enter this
ensemble without another inference run. From the eligible pool, validation chose
**Jev detailed, Kev brief, and Clef detailed**. We did not use test results to
choose the policy or make new edits. Earlier three-policy individual comparisons
remain in the full report as separate references.

## What happened on the test

There were 945 benign prompts and 754 harmful prompts. Balanced accuracy gives
equal weight to correctly allowing benign prompts and catching harmful ones.

| Frozen configuration | Balanced accuracy | False blocks | Missed harmful prompts |
|---|---:|---:|---:|
| Selected Jev individual | 88.69% | 47 | 133 |
| Majority vote: Jev + Kev + Clef | 88.71% | 53 | 128 |
| Decision-only logistic combination | 89.05% | 39 | 134 |
| **Score logistic combination — primary** | **89.32%** | **69** | **106** |
| Weighted score average — selected on validation | 89.08% | 76 | 104 |
| WildGuard 7B — historical reference | 89.81% | 51 | 113 |
| Prior PolicyLM + Shieldstral + CoPE ensemble — historical reference | 91.08% | 52 | 93 |

The primary score ensemble caught **27 more harmful prompts** than Jev, at the
cost of **22 additional false blocks**. Its balanced-accuracy gain was 0.63
percentage points, with a paired 95% interval from **−0.43 to +1.58**. That does
not resolve a clear improvement. Against WildGuard, its difference was −0.49
points, with an interval from −1.73 to +0.73.

The score-based logistic model also had a slightly higher balanced score than
the decision-only logistic model: a 0.27-point difference, with an interval
from −0.67 to +1.19. Keeping the scores gave the combiner more information, but
this run does not demonstrate a clear benefit from that extra information.

All these methods returned usable decisions for every test prompt. No failures
were removed from their denominators.

## A weighted average was possible—and did not guarantee a gain

We tested raw averages, calibrated averages, learned weights, logistic regression
on probabilities and log-odds, and a small random forest. The primary method was
declared in advance; we also selected a best score method using validation.

That validation selection favored a weighted average of **calibrated** component
scores: approximately **42.0% Jev, 25.8% Kev, and 32.2% Clef**. Its validation
balanced accuracy was 94.80%; its test score was 89.08%. Calibration functions and
weights were fitted only on training data, using group-separated out-of-fold
predictions for the weight fitting. These weights apply to this policy and
calibration setup; they are not general model-quality ratings.

An equal log-odds average had the highest observed test score among the new
three-model methods, at 89.74%. It was not the method selected as best on
validation. We report that result without promoting it after seeing the test.
It also remained below the historical specialist ensemble's 91.08% point estimate.

Jev's stored scores included exact zeros and ones. The log-odds methods therefore
used a clipping rule fixed before fitting; 806 Jev test scores required it.
These are transformed native probabilities, not raw logits from Jev's hidden
implementation. The primary probability-based logistic model required no such
transformation.

## What if the team needs open weights only?

We repeated the combinations with Kev and Clef, excluding the API-only Jev.
The open-only primary logistic model scored **87.52%**, compared with **86.91%**
for its validation-selected Kev individual. That 0.61-point improvement also
had an interval spanning zero.

The open-only method selected as best on validation was a random forest. It
reached **88.10%**, with 102 false blocks and 98 missed harmful prompts. It caught
more violations than the primary open-only combination, but blocked more benign
content. Neither result displaced the historical WildGuard or specialist-ensemble
reference. Open weights give a team a different deployment option; that is a
separate consideration from the measured accuracy.

Including Jev in the primary logistic combination raised the balanced score by
1.80 points relative to the open-only primary (paired interval +0.81 to +2.83).
That is evidence for these particular configured combinations, not a general
advantage of API models over open weights.

## The deployment targets were harder than the leaderboard

We made separate validation selections for a maximum 5% false-block burden and
for catching at least 90% of violations. Neither primary ensemble met either
corresponding target on test. The three-model configuration selected for the 5%
limit actually blocked **7.51%** of benign test prompts. The configuration selected
for the 90% catch target caught **83.42%** of harmful test prompts.

The decision-only logistic controls did meet the 5% false-block limit: the
three-model combination caught 82.23% of violations with 4.13% false blocks; the
open-only combination caught 72.28% with 4.55% false blocks. These are separate
validation-selected operating points. The [integrated comparison](../leaderboard/README.md)
shows their targets alongside the earlier models and ensembles.

The models' test scores were strongly correlated, about 0.89–0.90, and their
native decisions shared 89 errors across all three. Those are descriptive signs
of overlapping behavior, not an explanation of their internal architectures.
Adding models does not necessarily add enough independent information to justify
the additional serving and maintenance work.

For a moderation team, this experiment supports trying a small score combiner
when native probabilities are available, while keeping a strong individual-model
control and explicit error targets. It does not establish that an ensemble is
better, cheaper, or easier to operate. The combination needs labels, fitting,
validation, versioned policies and decision settings, and two or three model
evaluations for every production input.

## Evidence and reproduction

- [Registered protocol](PLAN.md) and [lab notes](NOTES.md).
- [Full result tables, equations, selected settings, and paired comparisons](../../published_runs/2026-10-30-decision-ensemble/RESULTS.md).
- [Evidence archive and CPU reproduction](../../published_runs/2026-10-30-decision-ensemble/README.md).
- [Integrated leaderboard](../../published_runs/2026-10-30-leaderboard-decision-ensembles/README.md): all nine combination methods per cohort alongside the earlier models and ensembles. Individual calibration controls and selection aliases remain in this study.
- [Metric definitions](../leaderboard/METRICS.md).

The archive retains every registered method, including regressions, plus all
validation grids and native test scores. Reproduction refits the small models and
checks the selections, scores, metrics, and uncertainty intervals. No underlying
language-model weights were updated. Earlier studies and their results remain
unchanged.
