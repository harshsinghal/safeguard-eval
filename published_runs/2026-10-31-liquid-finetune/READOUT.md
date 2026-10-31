# Can a small Liquid model learn to classify harmful prompts?

We fine-tuned **Liquid LFM2.5-Encoder-350M** on WildGuard and obtained **86.40%
test accuracy** with the configuration chosen on validation. The same encoder,
kept frozen and paired with a trained linear classifier, reached **82.22%**.
Across three fine-tuning seeds, accuracy averaged **86.23%**, ranging from
85.52% to 86.76%. We did not pick the most successful test seed.

That is a useful improvement over this model's frozen-feature control. It is
not a new best result for the repository, or a measurement of the model's
maximum possible accuracy.

[Complete results](RESULTS.md) · [All metrics as CSV](results.csv) ·
[Registered plan](PLAN.md) · [Reproduce the experiment](RUNNING.md) ·
[Frozen evidence](README.md)

## What changed this time?

In the [previous experiment](../../docs/contrastive-heads/README.md), the model turned
text into features, and we trained a small classifier to read those features.
The model producing them stayed unchanged.

Here we also updated the **encoder's weights**. The encoder and a binary
classification head learned together from harmful and benign training examples.
This is actual task-specific fine-tuning, rather than a policy edit or a new
classifier on fixed features. The resulting model takes a prompt and returns a
harmfulness score. It receives no policy document and generates no answer.

We chose Liquid's [350M bidirectional encoder](https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M),
which the provider designed for downstream classification and other tasks.
Our encoder plus head has 354,484,993 parameters. We followed the provider's
[encoder-plus-head pattern](https://github.com/Liquid4All/cookbook/tree/main/examples/lfm-encoder-classification),
with our own binary task, split controls and evaluation procedure. These are
open weights under the LFM Open License v1.0.

## What went into training and testing?

We used **4,096 labeled WildGuardTrain prompts** for fitting and **1,536** for
validation, reusing the earlier studies' exact group-disjoint populations.
This is a subset of WildGuardTrain, not the full training dataset. Validation
selected the learning rate, epoch and cutoff. We then froze those settings
before uploading any test prompts to the GPU. Test labels stayed local.

The final test contained **1,699 labeled WildGuardTest prompts**: 945 benign and
754 harmful. We evaluated prompt harmfulness only, not response harmfulness or
refusal behavior. The 26 source test prompts without a harmfulness label were
excluded, as in the earlier studies. Every retained prompt received a score.
No fitting, validation or test prompt required truncation at the 8,192-token cap.

There were two learning rates, three epochs per run and three seeds: 18
fine-tuned checkpoints. The frozen control tried five regularization settings.
Validation selected epoch 3 at learning rate 0.00005 for all fine-tuning profiles.
The primary objective was ordinary accuracy, with a shared cutoff of 0.68.

## What happened on the test set?

The table uses the predeclared primary seed, not the best seed found on test.
Both pipelines use their validation-selected accuracy settings.

| Pipeline | Accuracy | Balanced accuracy | Benign prompts falsely blocked | Harmful prompts missed |
|---|---:|---:|---:|---:|
| Frozen Liquid encoder + logistic regression | 82.22% | 80.88% | 68 / 945 | 234 / 754 |
| Fine-tuned Liquid encoder + linear head | **86.40%** | **85.49%** | **60 / 945** | **171 / 754** |

Fine-tuning produced **71 fewer errors** in the primary run. It corrected 117
cases that the frozen control got wrong, while introducing 46 new errors.
The accuracy gain was **4.18 percentage points**, with an exploratory paired
95% bootstrap interval of **2.71 to 5.65 points**. Both error types improved in
this primary run. All three fine-tuning seeds improved accuracy and missed fewer
harmful prompts, but one seed made two more false blocks than the frozen control.

For context, our earlier frozen PolicyLM linear classifier reached **88.82%**
accuracy, and the released WildGuard model reached **90.35%** on the same test
population. Those studies used different models and selection procedures. They
show that this bounded Liquid fine-tune did not exceed those recorded results;
they do not establish an inherent ranking of architectures or equal training
budgets. This experiment remains separate from the common leaderboard.

## A good validation setting is not a guarantee

Fine-tuned mean validation accuracy was **93.99%**, but mean test accuracy was
**86.23%**. The selected settings did not transfer perfectly. Training and test
also differ in sources and label provenance: WildGuardTrain uses GPT-4 labels,
while WildGuardTest uses human labels, as described in the
[dataset documentation](https://huggingface.co/datasets/allenai/wildguardmix).
This is a possible contributor to the
gap, not a cause established by this experiment.

We preserved a default-cutoff control. With the same primary checkpoint and a
cutoff of 0.5, test accuracy was **86.93%**, with 70 false blocks and 152 missed
harmful prompts. That was a predeclared supplementary evaluation. We keep the
validation-selected **86.40%** as the primary result instead of changing the
headline selection after seeing test scores.

The separately selected balanced profile used cutoff 0.86 and reached **84.64%
balanced accuracy** in the primary run. It made four fewer false blocks than
the primary accuracy profile, but missed 16 more harmful prompts. Validation
selection did not guarantee the better test balance either.

Operational targets also shifted. The fine-tuned setting selected to keep
validation false blocks at or below 5% produced a **5.82%** false-block rate
on test in the primary seed; all three seeds exceeded 5%. The setting selected
for at least 90% validation harmful recall achieved **73.21%** on test in the
primary seed; all three seeds missed the recall target. A validation target
must be checked again on deployment-relevant data.

## What does this mean for a moderation team?

A compact encoder can learn a useful fixed classification task from labeled
examples, and updating its weights improved this pipeline. It still required
training data, validation, checkpoint selection and a tested cutoff. A small
model and a fine-tuning run did not remove that work.

The policy boundary is now expressed through the **labeling specification and
training examples**, rather than supplied as a document at inference time.
If a platform changes that boundary, this experiment does not show that the
classifier can adopt the new policy without new evaluation and potentially
new training. Policy-guided models and task-specific classifiers offer different
ways to implement a policy; teams should compare them on the boundary and error
costs they actually care about.

This is a small, exploratory study. The public test has already been used in
our earlier experiments; it is not a fresh blind holdout. Pretraining exposure
to benchmark material is unknown. The frozen and fine-tuned pipelines have
linear heads at inference time, but different optimization and regularization,
so this is not a strictly optimizer-matched ablation. We tested one Liquid
checkpoint, a short training schedule and 4,096 fitting examples. Larger-data
training, HateXplain fine-tuning and a matched deployment latency comparison
were not run.

## Evidence and execution

All three selected checkpoints reproduced their stored validation scores
exactly when reloaded before test inference. The CPU verifier reselected all
eight operating profiles, reproduced 16 selected test metric rows and both
paired comparisons. The complete CSV also includes fixed-cutoff controls.
Independent reconstruction matched every split's exact input-file hash.

The [evidence bundle](README.md)
contains the selections, predictions, split identities, source, runtime records,
checkpoint hashes and billing. Source prompts and embeddings stay private;
large checkpoint weights are kept locally. GPU usage is reconciled in the
bundle's billing record and the repository's [compute notes](../../docs/COMPUTE.md).

Additional GPU cost was **$0.29**, including the search and
artifact collection. Cumulative accounted provider spend is **$17.09
of the $20 cap**. The GPU was terminated, its temporary SSH keys were removed,
and the provider reported no remaining instances. RunPod and paid inference
APIs were not used. These charges exclude label creation, engineering time and
local electricity.
