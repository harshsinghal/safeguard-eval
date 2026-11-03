# Code embeddings and Qwen for code and skill screening

**Completed. Code embeddings were a workable starting point for a source-file
classifier, but they did not improve our agent-skill benchmark. A small neural
head was not an automatic upgrade over a linear classifier.**

This follow-up tested the proposed idea directly: turn an artifact into a vector,
then learn a malicious/benign boundary from labeled examples. We also tested
Qwen 4B and 9B with a broader search over policy instructions. The models inspected
code and skill text as data; no benchmark artifact was executed or installed.

## What we built

We used two frozen Jina models: the older 161M bidirectional code encoder and a
newer 0.5B Qwen-Coder-derived embedding model. For each dataset, we trained both
logistic regression and a one-hidden-layer neural network on the resulting vectors.
Only the small classifier learned from our labels; Jina’s weights stayed frozen.
The selected neural heads have about 99,000–230,000 trainable parameters, on top
of the frozen embedding model.

Qwen took the other route: an authored decision rule in its system prompt. We
tested the original three policies plus a behavior checklist, paired benign and
malicious examples, and clearer scope/authority guidance. Ordinary networking,
authentication and scoped cleanup remained allowed. Covert data transfer, unrelated
destruction, deceptive output and malicious instruction overrides were blocked.
These were conceptual examples in the policy, not synthetic training rows.

Fitting labels trained the heads. Validation selected their settings and the
Qwen policies. Every choice was [published before new test inference](preparation/README.md).
There was no score calibration, test-based policy repair or best-seed selection.

## What happened on the held-out data

Balanced accuracy gives equal weight to catching malicious artifacts and allowing
benign ones. Code has 160 test files, balanced between classes; skills has 1,384
test texts from held-out sources. The scores should not be averaged across tasks.

| System | Code balanced accuracy | Skill balanced accuracy |
|---|---:|---:|
| Jina v2 code + logistic regression | 88.75% | 54.88% |
| Jina v2 code + small neural head | 88.75% | 48.49% |
| Jina code 0.5B + logistic regression | 84.38% | 57.26% |
| Jina code 0.5B + small neural head | 84.38% | 54.58% |
| Qwen3.5 4B · selected policy | 86.88% | 54.85% |
| Qwen3.5 9B · selected policy | 88.75% | 55.48% |

Neural rows use the first registered seed, 20261103. All three seeds and uncertainty
intervals are in the [full results](RESULTS.md). Every final output resolved.

**On code, the older Jina representation scored higher than the newer one in this
run.** Both linear and primary neural heads reached 88.75% with Jina v2 and 84.38%
with Jina code 0.5B. The primary neural heads exchanged false blocks for misses without
reducing the total errors. The earlier fine-tuned Liquid classifier scored 91.25%
and Jev 90.00%; this small, largely model-labeled test does not establish a precise
ranking between close systems. Qwen 9B also reached 88.75%, with zero false blocks
and 18 misses; Jina v2 with logistic regression made seven false blocks and
11 misses. Equal headline accuracy did not mean equal behavior.

**On skills, the validation promise did not carry through.** Jina code 0.5B with
logistic regression went from 79.30% validation balanced accuracy to 57.26% on the
source holdout. It falsely blocked 282 of 545 benign skills and missed 283 of 839
malicious ones. The corresponding neural result was 54.58%. All three neural seeds
were below the matching linear classifier for both Jina representations. The
previous character TF-IDF baseline remained stronger than these embedding heads
at 70.19%, though its own 258 false blocks still prevent a deployment-ready claim.

## Did the Qwen policy changes help?

Validation chose different policies for the two sizes. Qwen 4B retained the brief
code rule and chose scope/authority guidance for skills. Qwen 9B chose a behavior
checklist for code and paired examples for skills. That is evidence about model-
and task-specific selection, not proof that every extra clause helps.

| Model / task | Brief test BA | Selected test BA | Selected policy |
|---|---:|---:|---|
| qwen4 / code | 86.88% | 86.88% | brief |
| qwen4 / skills | 54.17% | 54.85% | scope |
| qwen9 / code | 86.25% | 88.75% | behavior |
| qwen9 / skills | 55.30% | 55.48% | contrasts |

For Qwen 4B on skills, the gain was only 0.68 percentage points on test despite
a larger validation gain. Its selected policy caught 83 of 839 malicious skills,
while falsely blocking one benign skill. Good benign allowance is only half
of a useful detector. Qwen 9B moved from 55.30% to 55.48% on skills, catching
95 malicious skills while falsely blocking two benign ones. Both skill-policy
change intervals include zero; neither is a resolved improvement in this analysis.

## What this means for the next design

A frozen embedding model plus a trained head is a legitimate way to build a
fixed-task classifier. It can be small and requires no additional backbone
fine-tuning. It still depends on labeled examples and does not inherit the
ability to apply an arbitrary new policy at inference time. Changing the learned
decision boundary normally requires another training/evaluation cycle.

This study also separates code retrieval quality from security-classification
generalization. A newer retrieval embedding and a more flexible head did not
guarantee a better detector. The large skill development-to-test gap is consistent
with a source-shift problem; it does not prove which dataset cues the model learned.
The [dataset publisher](https://github.com/protectskills/MaliciousSkillBench) reports
a similar difficulty under source-disjoint evaluation, using a different training
and input protocol. A useful future development test would hold out sources or
attack families within the development pool as well, keeping the final evaluation
separate. No such new experiment was run here.

For destructive actions or networking specifically, we would need trustworthy
behavior annotations and benign counterexamples. These binary labels do not
establish a separately validated detector for each capability. A network request
can be legitimate; its purpose, destination and authorization matter.

## Checks and limits

Input hashes, feature ordering and selected checkpoint reloads were checked.
After seeing the poor skill results, we added a numerical diagnostic on validation
examples only: re-encode them after a fresh model load and compare singleton
inference with the original batches. The diagnostic did not change selections or
predictions. All four checks passed: minimum cosine agreement exceeded 0.9998;
the largest component difference was 0.00469. These are numerical checks, not
proof of semantic generalization. The primary neural heads fitted 99.5–100% of
the skill training examples correctly, making the held-out gap particularly clear.
See the runtime records for the outcomes and tolerances.

Code labels are largely model-assisted. The skill split holds out sources, not
every structural family. The shared 8,000-byte view can omit decisive content,
and companion files were not inspected. Test populations are reused from the
previous study; they are not new independent confirmation. No production latency
or throughput claim follows from this run. Jina code 0.5B uses CC-BY-NC-4.0,
so the research comparison is not commercial deployment permission.

**Cost: $0.60 against a $4 ceiling.** The GPU was terminated;
no paid model API was used. Compact features and selected heads are retained
privately; public evidence contains hashes, policies, predictions, selections and
reproduction code. Earlier papers, articles and versioned skill releases were not
automatically rewritten.

[Full results](RESULTS.md) · [Policy edits and methods](METHODS.md) · [Registered plan](PLAN.md) · [Run it yourself](RUNNING.md) · [Frozen evidence](../../published_runs/2026-11-03-artifact-representations/README.md) · [Prior eight-system comparison](../malicious-artifacts/README.md)
