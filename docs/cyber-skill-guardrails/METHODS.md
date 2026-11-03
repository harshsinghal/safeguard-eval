# What these comparisons measure

These studies ask two different moderation questions. CyberSecEval supplies
requests for cyberattack assistance and benign requests that change a system.
MalSkillBench supplies agent packages labeled benign or malicious. We classify
their text; we do not generate an attack, install a skill or test exploitation.

## Keep policy changes separate from evidence changes

Every editable model receives three candidate policies: a short statement of
intent, a more detailed account of harmful behavior and legitimate uses, and
that account with contrasting examples. The additions distinguish actions such
as stealing secrets from sending approved data to the intended API, and sabotage
from requested cleanup. These are conceptual contrasts, not executable examples.

The same intent is delivered through the model's own interface: PolicyLM category
fields, decision-model Choice specifications, Shieldstral's classifier template,
or Qwen's system instruction. Llama Guard uses its native custom-category field.
Its default taxonomy is retained as a separate control. Prompt Guard is fixed;
it has no editable policy in this experiment.

Validation chooses a policy for each model and task. We then compare that policy
with the initial brief policy on held-out inputs. For skills, we also remove
companion files while keeping the selected policy and decision rule unchanged.
That second comparison measures the effect of available evidence.

## The fixed-task controls learn from labels

Jina code embeddings remain frozen. Logistic regression and a shallow neural
network learn the task from fitting examples, with validation selecting their
settings. Their supervised training is an additional resource, so these controls
must not be described as policy-only systems. The SKILL.md-only heads are trained
separately; they are not the same head with its input shortened.

## Read the scores within their boundaries

Both test sets are balanced. Accuracy therefore equals balanced accuracy, but
false-block and miss rates still show very different operational tradeoffs.
All unresolved cases remain in denominators. Grouped confidence intervals account
for related rows within our grouping; they do not cover unknown labeling errors,
pretraining exposure, or all future deployment conditions.

The MITRE-to-BLOCK mapping follows the benchmark's intended source task. A reviewed
fitting example about market and company research illustrates why some requests
can look legitimate under a different policy. We preserve published labels and
do not rewrite the policy to exploit their source formatting.

The skill cohort excludes packages that exceed 20 KB of serialized text, contain
binary content, or fail the static eligibility rules. Registry metadata is removed.
Related templates, near-identical documents and malicious wild authors stay in one
split. This leaves only three wild malicious packages in the final test, versus
251 generated and two tool-test packages. A strong result here is not a reliable
estimate of detection across the wild ecosystem.

The [plan](PLAN.md) records exact pins, eligibility rules, policy selection,
thresholds, head grids, seeds and the spending ceiling.
