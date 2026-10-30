# Reading the moderation leaderboard

The leaderboard asks two questions together: **do we catch violations, and do we
correctly allow compliant content?** A single accuracy score can hide a poor answer
to either question.

This guide defines the metrics used in the [main README](../../README.md#current-leaderboard)
and the [expanded results](../../published_runs/2026-10-30-leaderboard-decision-ensembles/RESULTS.md).
The exact implementation is in [metrics.py](../../evals/leaderboard/metrics.py);
the [archived implementation](../../published_runs/2026-10-29-leaderboard/source/evals/leaderboard/metrics.py)
preserves the procedure used for the original reanalysis.

## Start with the mistakes

Here **positive means BLOCK** and **negative means ALLOW**, according to the
benchmark's labels and our stated mapping. These words do not describe sentiment.

| What the benchmark says | What the system returns | Name |
|---|---|---|
| BLOCK | BLOCK | True positive (TP): a caught violation |
| ALLOW | ALLOW | True negative (TN): correctly allowed content |
| ALLOW | BLOCK | False positive (FP): a false block |
| BLOCK | ALLOW | False negative (FN): a missed violation |
| Either label | No usable decision | Unresolved: an error, reported separately |

A false-block **count** needs its denominator. In HateXplain, there are 1,330
non-hate posts and 594 hate posts. Blocking 100 non-hate posts means a 7.52%
false-block rate; missing 100 hate posts means a 16.84% miss rate. Equal counts
are not equal class error rates.

For WildGuard, our labels concern prompt harmfulness only. For HateXplain,
offensive-but-not-hateful and normal posts are both ALLOW under the evaluated
hate-speech rule. ALLOW here is not approval under every possible platform policy.

## What each metric tells you

| Metric | Plain-language meaning | How to use it |
|---|---|---|
| **Balanced accuracy** | Average of the violation-catch rate and compliant-content allow rate. | Our headline comparison. It gives both classes equal weight even when one is larger. Higher is better. |
| **Recall / catch rate** | Share of all violations correctly blocked. | Check how much violating content escapes. Higher is better. |
| **Specificity / correct-allow rate** | Share of all compliant content correctly allowed. | Check whether legitimate activity can proceed. Higher is better. |
| **False-block rate / FPR** | False blocks divided by all compliant items. | Lower is better. This is not the share of the model's blocks that were wrong. |
| **Miss rate / FNR** | Violations incorrectly allowed divided by all violating items. | Lower is better. Unresolved violations are recorded separately. |
| **Precision** | Correct blocks divided by all returned BLOCK decisions. | Of the items stopped, how many actually violated this rule? Sensitive to the prevalence of violations. |
| **Ordinary accuracy** | Correct decisions divided by all test items. | Useful overall agreement, but the larger class contributes more. |
| **Macro-F1** | Average of the ALLOW-class and BLOCK-class F1 scores. Each F1 combines precision and recall. | A second summary that weights the two classes equally. It is not balanced accuracy. |
| **MCC** | Matthews correlation coefficient: a summary using all four binary confusion counts. | Ranges from −1 to +1; +1 is perfect, 0 indicates no binary correlation. We leave it unavailable if any output is unresolved. |
| **Coverage** | Share of test items with a usable ALLOW/BLOCK decision. | Check whether apparent quality depends on avoiding difficult cases or failing to answer. |
| **AUROC** | How well scores rank violations above compliant items across cutoffs. | Helps distinguish ranking quality from the chosen cutoff. Does not establish a deployable error rate or calibrated probability. |
| **Average precision (AP)** | A summary of precision and recall as the cutoff changes, weighted by recall increments. | Useful when violations are uncommon. Depends on prevalence; do not compare it across different populations without context. |

The full JSON also records **compliant error rate**, which combines false blocks
with unresolved compliant cases, and **violation error rate**, which combines
misses with unresolved violations. These equal one minus specificity and one
minus recall, respectively. FPR and FNR alone do not include unresolved outputs.

## A real example: Jev on HateXplain

The balanced-selected Jev configuration caught 470 of 594 hate posts: **79.12%
recall**. It correctly allowed 1,033 of 1,330 non-hate posts: **77.67%
specificity**. The average is **78.40% balanced accuracy**. It made 297 false
blocks, missed 124 hate posts, and returned no unresolved outputs.

An earlier configuration selected for ordinary accuracy missed 238 hate posts
and made 134 false blocks. Its ordinary accuracy was higher, but its catch rate
was much lower. Neither metric changed the labels; the selection objective
changed the policy and cutoff chosen for the system. See the
[selection comparison](README.md#why-some-numbers-changed-from-our-earlier-reports).

## Three views, three different objectives

The leaderboard does not select whichever configuration looks best on test.
It selects one configuration per entry **on validation**, freezes it, and then
reports that choice on test. Each view makes a separate selection:

| View | Validation selection rule | What to inspect on test |
|---|---|---|
| **Balance both classes** | Maximize balanced accuracy. | Both class error rates, coverage, and uncertainty. |
| **False-block limit: 5%** | Maximize recall among configurations with compliant error rate at most 5%. | Whether the limit still holds, and how many violations are caught. |
| **Violation-catch target: 90%** | Minimize compliant error rate among configurations with recall at least 90%. | Whether the catch target still holds, and the resulting false-block burden. |

Including unresolved compliant cases in the 5% constraint prevents failures from
making the limit easier to meet. If no candidate qualifies on validation, that
entry has a gap in that view. Passing validation does not guarantee passing test.

The common validation populations are 512 WildGuard prompts and 1,920 HateXplain
posts. Earlier fitting sizes, policy searches, and candidate counts differ by
study. Previously fitted calibrators and combiners are reused, not retrained for
this reanalysis. The integrated comparison has **261 eligible candidate records**,
producing 38 WildGuard entries and 20 HateXplain entries. The 52 newly included
records cover seven score-combiner families and two decision-only controls for
each decision-model cohort. They do not represent 52 new models. Their supervised
combiners were fitted in the source experiment, not during leaderboard integration.

The decision-model study's individual calibration controls and “best method”
aliases stay in that study's report. They are not extra leaderboard entries, and
they do not replace earlier individual-model selections. The detailed policy
without examples was selected for Jev and Clef in the new ensemble study;
example-bearing policies lacked fitting scores. This pool differs from the
previous individual comparison, where all three policy versions were eligible.

For scored candidates, the procedure considers the archived native decision and
cutoffs from 0 to 1 in steps of 0.01, plus a value just above 1. A score at or
above the cutoff becomes BLOCK. Categorical outputs without scores cannot be
re-thresholded. Deterministic tie-breaks prefer better weaker-class recall, then
macro-F1, then native decisions and cutoffs near 0.5; the exact ordering,
including secondary objectives for the constrained views, is recorded in the code.

Balanced accuracy is a comparison tool, not a statement that the two mistakes
have equal business cost. A team may prefer a false-block constraint, a minimum
catch rate, or a cost function tied to its own workflow. That requirement belongs
in validation selection before inspecting the final test result.

## Unresolved outputs and missing scores

All test items remain in accuracy and class-recall denominators. An API failure,
unusable response, or invalid score never becomes a correct REVIEW decision.
The WildGuard Safeguard row has nine unresolved outputs: two on ALLOW cases and
seven on BLOCK cases. The other headline rows have none.

AUROC and AP require numerical scores. We calculate them only for items with a
finite score and a usable decision, report **score coverage**, and leave them
unavailable if the valid subset does not contain both classes. Score coverage
and decision coverage are distinct. We do not invent probabilities for a model
that supplied only a category. The majority-vote controls therefore have no
AUROC or AP. A logistic combiner of decisions does produce a numerical score;
its ranking metrics describe that fitted combiner, not native confidence from
its component models. Native probabilities and transformed log-odds are also
distinct from a model's full vocabulary logits or a calibrated real-world risk.

<details>
<summary>Exact formulas, including unresolved outputs</summary>

Let EA and EB be unresolved outputs on gold ALLOW and gold BLOCK items.
Let P = TP + FN + EB, N = TN + FP + EA, and total = P + N.

- Recall = TP / P; specificity = TN / N.
- Balanced accuracy = (recall + specificity) / 2.
- FPR = FP / N; FNR = FN / P.
- Compliant error rate = (FP + EA) / N; violation error rate = (FN + EB) / P.
- Precision = TP / (TP + FP); accuracy = (TP + TN) / total.
- BLOCK F1 = 2TP / (2TP + FP + FN + EB).
- ALLOW F1 = 2TN / (2TN + FP + FN + EA).
- Macro-F1 = (BLOCK F1 + ALLOW F1) / 2.
- Coverage = (total − EA − EB) / total.
- For complete binary outputs, MCC = (TP×TN − FP×FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN)).

The F1 convention treats an unresolved answer as a missed prediction of its gold
class, with no invented prediction of the other class. Undefined class F1 is
zero in the macro average. MCC is unavailable with unresolved outputs and is
zero for a degenerate complete binary confusion matrix. Balanced accuracy is
unavailable for a slice containing only one gold class; inspect the relevant
class recall instead.

</details>

## Confidence intervals and slices

The full report uses 2,000 bootstrap draws, resampling duplicate groups rather
than separating identical items. The same draws are used for compared systems,
which gives a **paired** interval for their score difference. If that interval
includes zero, the observed ordering does not resolve a clear difference under
this analysis. Comparing two separate intervals is not a substitute for the
paired comparison.

These are descriptive, unadjusted 95% intervals conditional on the saved
predictions. They do not account for all policy searches, repeated model runs,
label ambiguity, or multiple comparisons. The tests are public and have been
examined in earlier studies. A narrow interval does not make this a new blind
evaluation or establish performance on an enterprise's own traffic.

The JSON and interactive report also expose subgroup results, including
WildGuard subcategories and adversarial status, and HateXplain source labels,
platforms, and annotation agreement. Check denominators and both error types;
small slices can be unstable. The leaderboard measures classification quality,
not a controlled comparison of latency, GPU requirements, privacy, or cost.
