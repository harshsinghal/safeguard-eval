# Jev still needs a policy—and a decision about mistakes

Jev was competitive in these two tests, but it did not establish a general
advantage over our earlier policy models. Its strongest lesson was familiar:
the instructions and the decision threshold changed the outcome substantially.

We evaluated Jev 1.14 through OpenRouter. Its interface accepts text, a question,
and descriptions of the permitted answers. It returns a choice and probabilities
instead of writing a response. That makes it convenient to use as a classifier.
It does not mean that every classification is correct, or that “System One” is
itself an explanation for better benchmark performance.

## The same tasks as before

We used the same **1,699 labeled WildGuardTest prompts** and **1,924 HateXplain
test posts** as our earlier studies. WildGuard asks whether a user's request is
harmful. HateXplain asks whether a post is hate speech; under this particular
binary rule, offensive-but-not-hateful and normal posts count as ALLOW. We did not
evaluate response refusal, response harmfulness, image moderation, or REVIEW
routing.

We tried three versions of the question Jev receives:

1. **Brief:** a concise description of the task and the two answer classes.
2. **Detailed:** our original baseline policy's definitions, conditions, and
   exceptions, delivered through Jev's native instructions and answer criteria.
3. **With examples:** the detailed version plus four labeled training examples
   that the detailed version had misclassified—two BLOCK and two ALLOW.

The examples were selected by a fixed rule from fitting data. Validation picked
the version to use, then separately picked a score threshold. Both decisions
were frozen before test inference. No model weights changed. This was a small
three-candidate search, not a claim to have found Jev's maximum possible accuracy.

## What happened

| Jev configuration | WildGuard accuracy | HateXplain accuracy |
|---|---:|---:|
| Brief policy, native choice | 89.35% | 69.33% |
| Detailed policy, native choice | 90.05% | 72.77% |
| Detailed policy + training examples, native choice | 90.17% | 75.16% |
| Selected policy + validation-chosen threshold | 89.94% | 80.67% |
| Brief policy + its own validation-chosen threshold | 89.35% | 79.47% |

Validation selected the version with examples for both tasks. “Selected policy”
therefore means **the candidate that performed best on validation**, not a policy
chosen after seeing these test scores.

On WildGuard, the wording changes produced a modest observed gain. The final
threshold adjustment actually lost four correct classifications compared with
the selected policy's native choice. We retain that result because the threshold
was chosen before testing; replacing it after seeing the test would overstate the
success of our procedure.

On HateXplain, the policy changes raised native-choice accuracy by **5.82
percentage points**. Adding the threshold adjustment raised it further. But the
brief policy also reached **79.47%** with threshold selection alone. The final
80.67% result should not be described as an 11-point gain caused only by better
policy writing. Against the equally threshold-tuned brief control, the difference
was **1.20 points**.

Threshold tuning here changes the cutoff used to act on a score. It does not
change Jev's probabilities or train a calibration model.

## The higher score conceals a consequential trade-off

For the selected HateXplain policy, threshold tuning reduced false blocks from
**390 to 134**. It also increased missed hate-speech posts from **88 to 238**.

That trade improved overall accuracy because non-hate posts are more common in
this test. Yet hate-speech recall fell from **85.19% to 59.93%**. The final
macro-F1 was **76.11%**, while the hate-class F1 fell from **67.92% to 65.68%**
when the threshold was applied. A team focused on catching hate speech might
reject the configuration with the higher accuracy.

This is a policy and operations decision, not simply a model-selection decision.
Someone has to decide how much mistaken blocking and missed abuse the workflow
can tolerate, then select the validation objective accordingly. We optimized
accuracy in this registered experiment and preserved its consequences.

## How it compares with our earlier results

The released WildGuard model scored **90.35%** on the same WildGuardTest rows.
Jev scored **90.17%** with its selected policy and native choice, or **89.94%**
with the frozen threshold. The earlier specialist log-odds ensemble scored
**91.29%**. Jev did not outperform those configurations here.

On HateXplain, Jev's final **80.67%** was above the earlier calibrated Shieldstral
individual's **79.57%** and close to the specialist-plus-Qwen ensemble's
**80.82%**. Its difference from Shieldstral was **+1.09 points**, with an
unadjusted paired 95% interval of **−0.78 to +2.96**. Its difference from that
ensemble was **−0.16 points**, with an interval of **−1.82 to +1.56**. These
comparisons do not establish a clear winner.

The earlier models used different development budgets, policies, and in some
cases learned calibrators or ensembles. We are comparing complete configurations,
not isolating the effect of Jev's architecture. The public test sets have also
been reused, and prior exposure during model training is unknown.

## What we can take from this

Yes, Jev can be adapted through written instructions, class descriptions, and
examples. It belongs in the comparison. Its typed interface was reliable in this
run: all benchmark responses parsed and came from the expected model/provider.
There were still classification errors.

For a practitioner, the useful question is whether a particular Jev configuration
meets the team's error tolerances and operating constraints. The System One label
does not replace that evaluation. Neither does a single aggregate accuracy score.

We made **8,103 benchmark requests**, producing **22,261 classifications** across
the policy variants, plus one synthetic connectivity request. The total API charge
was **$0.424208**, with no GPU rental. Median client-observed request latency was
**0.323 seconds** and p95 was **0.552 seconds**, with up to eight concurrent
requests and two or three policy questions per request. This was not a matched
latency or total-cost comparison against our earlier self-hosted models.

See the [full results](RESULTS.md), [registered plan](PLAN.md),
[experiment notes](NOTES.md), and
[reproducible evidence](../../published_runs/2026-10-29-jev/README.md).
