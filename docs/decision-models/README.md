# Kev and Clef: open decision models still need policy and cutoff testing

Follow-up: the [WildGuard decision-score ensemble study](../decision-ensemble/README.md)
combines Jev, Kev, and Clef scores, with an open-only Kev/Clef cohort and
decision-only controls. It reuses these saved outputs and preserves this study.
The [current integrated leaderboard](../../published_runs/2026-10-30-leaderboard-decision-ensembles/README.md)
adds those combinations to the comparison.

We tested **Kev 4B** and **Cloudflare Clef-Flash 9B** on the same WildGuard and
HateXplain examples used for Jev. Both worked as self-hosted classifiers, without
any additional fine-tuning. Their observed balanced scores were below Jev's in
this bounded comparison. The more useful finding is how differently they
responded to the policy text.

**Kev selected a short policy for both tasks. Clef selected a policy with
examples, together with a different decision cutoff for each task.** More detail
was useful for one model and damaging for the other on HateXplain. A decision
model's default probability cutoff could also hide the value of a policy edit.

The [leaderboard accompanying this study](../../published_runs/2026-10-29-leaderboard-decision-models/index.html)
contains **20 entries per benchmark** and 209 eligible candidate records.
The previous 18 entries retain their original selections and results. The
[complete tables](../../published_runs/2026-10-29-leaderboard-decision-models/RESULTS.md)
include ordinary accuracy, macro-F1, MCC, error rates, and uncertainty.

## What we tested

WildGuard asks whether a user's request is harmful. We evaluated **prompt
harmfulness only**, not response safety or refusal behavior. HateXplain asks
whether a post contains hate speech. Its normal and offensive-but-not-hateful
posts are both ALLOW under our binary policy.

| Benchmark | Fitting examples | Validation examples | Test examples |
|---|---:|---:|---:|
| WildGuard | 1,024 | 512 | 1,699 |
| HateXplain | 1,024 | 1,920 | 1,924 |

Both models used their released classification heads and native Choice input.
We supplied the text to assess, a policy instruction, and definitions for ALLOW
and BLOCK. We did not ask a chat model to generate a label, update model weights,
train a new ensemble, or fit a new probability calibrator.

We froze the selections on validation before uploading test data to the GPU.
These public tests have been used in our earlier research, so this remains an
exploratory extension, not a fresh blind benchmark. Split hashes, implementation
hashes, and selection timestamps are in the [evidence archive](../../published_runs/2026-10-29-decision-models/README.md).

## What “policy optimization” meant here

Each model had the same three-candidate budget as Jev:

1. **Brief:** a short task question and definitions of the two classes.
2. **Detailed:** the same fuller policy used in the Jev study. WildGuard adds
   concrete harm categories and distinguishes benign discussion from requests
   for harmful output, including disguised requests. HateXplain adds target,
   stance, quotation and condemnation exceptions, and the distinction between
   attacking people and criticizing a belief, institution, or government.
3. **Examples:** the detailed policy plus four short labeled fitting examples,
   two for each class. A fixed rule preferred this model's fitting errors and
   unanimous HateXplain annotations. Thus the examples could differ by model.

The detailed edits were tested as a bundle. We cannot attribute an effect to
one particular sentence or exception. The example labels came from the benchmark;
they were not independently adjudicated by a new policy-review team.

For every candidate, validation also tested possible BLOCK cutoffs. The main
selection maximized **balanced accuracy**, the average of the violation catch
rate and the compliant-content allow rate. Separate selections tested a 5%
false-block limit and a 90% violation-catch target. None used test results to
choose a policy or cutoff.

## How the selected systems performed

The table uses validation-selected configurations, not each model's largest
observed test score.

| Benchmark | Model | Balanced accuracy | Ordinary accuracy | False blocks | Missed violations |
|---|---|---:|---:|---:|---:|
| WildGuard | Jev 1.14 | 88.69% | 89.41% | 47 | 133 |
| WildGuard | Clef-Flash 9B | 87.62% | 87.99% | 86 | 118 |
| WildGuard | Kev 4B | 86.93% | 87.58% | 69 | 142 |
| HateXplain | Jev 1.14 | 78.40% | 78.12% | 297 | 124 |
| HateXplain | Kev 4B | 75.17% | 74.69% | 347 | 140 |
| HateXplain | Clef-Flash 9B | 74.94% | 76.04% | 295 | 166 |

WildGuard has 945 compliant and 754 harmful test prompts. HateXplain has 1,330
non-hate and 594 hate posts. Error counts therefore need their denominators.
For example, Clef caught more WildGuard violations than Jev but falsely blocked
more compliant prompts. On HateXplain, Clef had fewer false blocks than Kev but
missed more hate posts. Ordinary accuracy and balanced accuracy consequently
rank those two HateXplain configurations differently.

Jev's balanced advantage over Kev was **1.76 points on WildGuard** (paired 95%
interval +0.33 to +3.26) and **3.23 points on HateXplain** (+1.29 to +5.14).
Its advantage over Clef was **1.07 points on WildGuard** (−0.27 to +2.43) and
**3.46 points on HateXplain** (+1.32 to +5.41). The WildGuard comparison with Clef
does not resolve a clear difference. Kev and Clef are also not clearly separated
from each other on either task. These are descriptive, unadjusted intervals.

Neither new model displaced the earlier leading ensembles or exceeded the
released WildGuard model's 89.81% balanced score on WildGuardTest. Kev's 86.93%
was close to the previously tested Qwen 4B configuration's 86.81%; that small
observed difference is not evidence of a decision-architecture advantage.

## The policy result is more interesting than the ranking

Consider HateXplain. At their native decision rule, the same move from the short
to the detailed policy changed Kev's balanced accuracy from **70.22% to 61.98%**.
Kev made fewer false blocks, but missed far more hateful posts. Even after each
policy received its own validation-selected cutoff, the short policy scored
75.17%, compared with 65.93% for the detailed policy. This was not simply a
default-cutoff problem: the score's ability to rank hate above non-hate also
declined, with AUROC falling from 0.815 to 0.724.

Clef tells a different story:

| Clef policy on HateXplain | Native balanced accuracy | With its validation-selected cutoff |
|---|---:|---:|
| Brief | 68.00% | 71.25% |
| Detailed | 67.01% | 73.51% |
| Detailed + four examples | 65.93% | 74.94% |

At the native decision rule, the example policy overblocked 819 non-hate posts.
Using its frozen 0.88 cutoff reduced that to 295, while missed hate posts rose
from 39 to 166. The example policy also ranked the two classes better: AUROC
increased from 0.772 for the brief policy to 0.816. After each policy received
its own validation-selected cutoff, the example policy exceeded the brief one
by **3.69 balanced points** (paired interval +2.04 to +5.38).

That comparison changes **both policy and cutoff**. It would be misleading to
describe the entire gain as an improvement from writing more words. It would
also be misleading to discard the example policy solely because its native
accuracy was lower. The policy changes the scores; the cutoff determines how
those scores become actions.

Validation selection can disappoint too. Kev's selected WildGuard cutoff scored
86.93%, slightly below the brief policy's native 87.37%. We retain the selected
result rather than replacing it after seeing the test answers.

## Operational targets remain difficult

For WildGuard, neither new model's selected configuration met its 5% false-block
limit or 90% catch target on test. For HateXplain, Clef's low-false-block
configuration met the 5% limit, but caught only **29.29%** of hate posts. Kev's
corresponding configuration caught 31.48% with a 6.32% false-block rate, missing
the limit. Neither met the 90% catch target on test; those configurations
falsely blocked about 48% of compliant HateXplain posts.

A validation target is therefore a requirement to test again, not a production
guarantee. WildGuard's validation sample comes from model-labeled WildGuardTrain,
while its official test uses human annotations and a different mixture.

## What this adds to the research

We now have two tested open-weight alternatives to a hosted decision API. Their
native interfaces produced usable probabilities and complete binary outputs.
This gives practitioners additional deployment options, but does not establish
that System 1 models are generally more accurate, safer, or cheaper than policy
specialists or general-purpose LLMs. Jev's internal architecture and size remain
undisclosed in the sources we reviewed.

The practical lesson is to **validate the policy, interpreter, and cutoff
together**. More detailed instructions are not automatically better. A policy
that works with one model can change another model's mistakes in an unwelcome
direction. This study varies wording within each model; it does not add a new
complete cross-model transfer matrix.

Historical training exposure is not fully known. Kev's disclosed training
includes Aegis content-safety data; neither an absence of named benchmark data
in a model card nor an open checkpoint proves no prior exposure. Earlier
models had different authoring budgets and inference setups. The benchmark is
English, binary text classification, not image moderation, a human-review route,
or an enterprise access-control system.

## Cost, verification, and reuse

Both models ran on one GPU.ai RTX6000 Ada 48GB GPU. **44,522 classifications**
were saved across all stages, with zero unresolved outputs and matching remote
prediction hashes. Single-item/batched checks agreed on all six fitting cases
per model; their maximum probability differences were 0.00359 for Kev and
0.00101 for Clef. This small check does not establish exact numerical equivalence
on every possible input. Both used BF16; Kev's published FP32 reference path
was not reproduced.

The provider recorded **$0.87** for 4,832 GPU-seconds. Cumulative recorded spending
is **$13.7954 of the authorized $20**, leaving about $6.20. Termination was
verified, the account had no active GPU.ai instances afterward, and temporary
SSH keys were removed. RunPod was not used. These are experiment costs, including
setup, not a matched production-cost comparison or a provider endorsement.

Read the [frozen plan](PLAN.md), [native-inference guide](RUNNING.md),
[evidence archive](../../published_runs/2026-10-29-decision-models/README.md), and
[expanded leaderboard](../../published_runs/2026-10-29-leaderboard-decision-models/README.md).
Model references: [Kev](https://huggingface.co/jaredpalmer/kev-4b) and
[Clef-Flash](https://huggingface.co/Cloudflare/clef-flash).
