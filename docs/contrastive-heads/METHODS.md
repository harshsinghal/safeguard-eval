# What the small classifiers learn

Each submitted text becomes a fixed vector of numbers. PolicyLM provides a
representation at its native policy-category position; ModernBERT provides the
average final representation across content tokens. Neither backbone changes
while the task classifier is trained.

The three classifier arms answer separate questions:

| Comparison | Question |
|---|---|
| Logistic regression versus a small ordinary neural network | Does a more flexible decision boundary help on the same features? |
| Ordinary versus contrastive neural network | Does teaching same-label examples to have similar learned representations help beyond that flexibility? |
| PolicyLM versus ModernBERT features | Which complete fixed-feature configuration works better here? This does not isolate architecture, size, specialization or policy conditioning. |

Both neural networks have the same layers, initialization seeds, batches,
optimization schedule and validation search. The contrastive version adds one
training objective: examples with the same label are encouraged to have similar
64-dimensional representations, and differently labeled examples are separated.
That representation is learned by the small network; the input embeddings remain
fixed. The ordinary classifier still supplies the allow/block supervision in
both versions. There are no generated augmentations or hand-picked difficult
pairs, and no test errors are fed back into training.

All four task/backend combinations use the same assigned fitting and validation
examples within a task. Labels fit the classifiers; validation chooses settings
and decision cutoffs. Three seeds give three separately trained neural models.
We select settings by their mean validation performance and use one shared cutoff.
The first seed is declared in advance as the primary point result. The others
show variability; we neither select the best test seed nor average their scores
into an ensemble.

## Four different operating goals

- **Balanced:** maximize the average of correctly allowing compliant examples
  and catching violations, giving both classes equal importance.
- **Accuracy:** maximize the proportion of all examples classified correctly.
  A more common class has more influence on this objective.
- **False-block limit:** obtain the highest recall while every seed meets a 5%
  false-block limit on validation.
- **Catch target:** obtain the lowest false-block rate while every seed catches
  at least 90% of violations on validation.

Each goal selects its own settings and cutoff before test scoring. A validation
constraint may fail on test. Raw sigmoid or logistic scores are not automatically
calibrated probabilities of harm; Brier score and log loss are also reported.

## Scope and interpretation

This is a bounded comparison on 4,096 fitting examples per task, not an attempt
to establish each architecture's best possible accuracy with unlimited data or
search. ModernBERT is a pretrained masked-language encoder, not a task-fine-tuned
moderation model or a retrieval-tuned sentence embedding model. Its published
fine-tuning results do not predict frozen-feature results in this experiment.

The PolicyLM configurations receive fixed prior policy text through the native
interface; ModernBERT receives submitted content alone. The trained head learns
the benchmark's fixed boundary from labels. We do not test whether a changed
policy is followed without retraining. WildGuardTrain and WildGuardTest also
differ in label provenance and data mixture. Public checkpoint exposure to these
benchmarks is unknown. Approximate duplicate-group exclusions do not establish
complete semantic deduplication or remove ambiguity in the source labels.

The public test sets have been used in prior studies. Frozen choices and paired
intervals make the follow-up auditable but do not restore a pristine blind test.
An independently labeled future holdout remains necessary for stronger claims
about production moderation, enterprise intent or new policies.

[Protocol and exact settings](PLAN.md) · [Reproduction](RUNNING.md) ·
[Metric definitions](../leaderboard/METRICS.md)
