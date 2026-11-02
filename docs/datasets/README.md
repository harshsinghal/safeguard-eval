# Dataset directory

[Research notebook](../../README.md) · [Model directory](../models/README.md) · [Metric definitions](../leaderboard/METRICS.md)

This is the inventory of data used in Safeguard Eval. Each entry explains what
the source contains, the decision we asked models to make, and where to find our
methods and results. A dataset's original task and our evaluation task are not
always the same.

## Find a dataset by task

| Dataset / source | What it helps test | Our evaluated population | Evidence |
|---|---|---|---|
| [WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix) | Harmful requests, harmful responses and refusals; we use **prompt harmfulness only** | 1,699 labeled WildGuardTest prompts | [Methods](../wildguard/METHODS.md), [leaderboard](../../README.md#current-leaderboard) |
| [HateXplain](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain) | Hate speech, offensive speech, target groups and annotation rationales | 1,924 official test posts, mapped to hate versus non-hate | [Study](../hatexplain/READOUT.md), [leaderboard](../../README.md#hatexplain-hate-versus-non-hate) |
| [Deepset prompt injections](https://huggingface.co/datasets/deepset/prompt-injections) | Injection-labeled text versus ordinary requests | 116 original test examples | [Earlier pilot](../../evals/injection/README.md), [six-model study](../prompt-injection/README.md) |
| [xTRam1 Safe-Guard prompt injection](https://huggingface.co/datasets/xTRam1/safe-guard-prompt-injection) | A larger, largely synthetic binary injection collection | 2,060 original test examples | [Six-model study](../prompt-injection/README.md) |
| [NotInject](https://huggingface.co/datasets/leolee99/NotInject) | False alarms on benign text containing suspicious words or characters | 339 benign examples | [False-block results](../prompt-injection/RESULTS.md#notinject-339-benign-lookalikes) |
| [JailbreakBench attack artifacts](https://github.com/JailbreakBench/artifacts) | Detection of released jailbreak attempts | 182 GCG/PAIR attempts targeting Vicuna-13B | [Detection results](../prompt-injection/RESULTS.md#jailbreakbench-182-released-attack-attempts) |
| [DiffusionDB](https://huggingface.co/datasets/poloclub/diffusiondb) | Browsing image-generation prompts and trying a custom policy | Interactive text-prompt demo; no scored policy test set | [Original application](../../DEMO.md) |

The first six rows are evaluation sources. DiffusionDB supported the original
demo. Our separately authored synthetic sets and serving workloads are listed
below. **No study here evaluates generated images.**

## WildGuardMix / WildGuardTest

**What it contains.** Ai2's collection includes user requests and assistant
responses, with separate annotations for prompt harmfulness, response
harmfulness and whether the response refuses. It provides `wildguardtrain` and
`wildguardtest` configurations. See the [dataset card](https://huggingface.co/datasets/allenai/wildguardmix)
and [WildGuard paper](https://arxiv.org/abs/2406.18495).

**Our task.** Read only the user prompt. Map harmful to BLOCK and benign to ALLOW.
We do not give the classifier the assistant response, gold risk category or
label, and we do not score response safety or refusal detection. Of 1,725
official test records, 26 lack a prompt-harmfulness label. The retained test has
**754 harmful and 945 benign prompts**.

**How we use it.** Policy editing, generalist comparisons, policy transfer,
ensembles, decision models, representation classifiers, Liquid encoder
fine-tuning, retrieval and serving studies all draw on this source. Development
samples come from WildGuardTrain. Their sizes differ: the original policy study
used 1,024 fitting and 512 validation examples; several later studies used 4,096
and 1,536. There is no single project-wide “WildGuard validation set.”

**Interpretation.** Training labels are model-assisted, while official test
labels are human annotations. The public test has been reused across studies;
the studies still select settings on development data, but are not independent
confirmations on newly collected tests. Unknown upstream model exposure is a
separate limitation. See [methods](../wildguard/METHODS.md),
[model exposure](../wildguard/MODEL_EXPOSURE.md) and the
[original evidence bundle](../../published_runs/2026-10-24-wildguard/README.md).
Access to source files requires accepting the publisher's conditions.

## HateXplain

**What it contains.** Social-media posts with hate, offensive and normal labels,
annotator votes, target-community information and text rationales. The
[Hugging Face card](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain),
[official data repository](https://github.com/hate-alert/HateXplain) and
[paper](https://arxiv.org/abs/2012.10289) describe the annotation task.

**Our task.** Use the majority class: **hate → BLOCK; offensive and normal →
ALLOW**. This tests a policy against hate speech, not a policy against every
offensive expression. Models receive the original tokens joined into text,
without annotation rationales or votes. The test has **594 hate, 548 offensive
and 782 normal posts**. We do not evaluate rationale extraction or the original
three-class task.

**Splits and use.** The official split files used here contain 15,383 training,
1,922 validation and 1,924 test posts. The structure study retained 1,920
validation posts after duplicate-group quarantine and used 1,024 fitting posts.
Later ensemble and classifier studies use their own documented development
cohorts. All retain the same 1,924-row official test. Experiments cover policy
components, formatting, transfer, generalist and decision-model comparisons,
ensembles, and trained heads on frozen features.

See the [readout](../hatexplain/READOUT.md),
[data importer and mapping](../../evals/hatexplain/data.py) and
[frozen study](../../published_runs/2026-10-26-hatexplain/README.md). Missing
conversation context and annotator disagreement matter; these results do not
establish fairness across all groups or languages.

## Deepset prompt injections

**What it contains.** Short texts labeled `1` for injection and `0` for
non-injection. The [source](https://huggingface.co/datasets/deepset/prompt-injections)
has **546 training and 116 test examples**. The test contains 60 injection labels
and 56 non-injection labels.

**Our task and use.** Map `1` to BLOCK and `0` to ALLOW. The earlier pilot removed
five overlapping training rows, then used the remaining 541 for development.
The newer [six-model study](../prompt-injection/README.md) combined eligible
Deepset and xTRam1 training examples for policy development, while reporting
their original tests separately. Both studies retained all 116 test rows.

Some source labels depend on an unstated application context: a task change or
role-play request is not necessarily an instruction-boundary attack. Scores
measure agreement with the supplied labels. Our [provenance record](../../evals/injection/provenance.json)
also notes conflicting license metadata in the source card; consult the
publisher before redistributing its text.

## xTRam1 Safe-Guard prompt injection

**What it contains.** A largely synthetic collection of ordinary instructions
and injection-labeled prompts, with **8,236 training and 2,060 test examples**.
The [dataset card](https://huggingface.co/datasets/xTRam1/safe-guard-prompt-injection)
describes its construction. This dataset is separate from OpenAI's GPT-OSS
Safeguard model despite the similar name.

**Our task and use.** Binary ALLOW/BLOCK classification using the source labels.
The test has **650 injection labels and 1,410 non-injection labels**. For the
six-model study, an overlap audit across evaluation material excluded 333
xTRam1 and three Deepset training rows. We then reserved 256 fitting and 256
validation examples: 64 per source/class in each split. No official test rows
were used to revise or select policies.

The source includes some harmful requests without a visible instruction
override. That limits interpreting its score as pure injection detection. See
the [dataset audit](../prompt-injection/preparation/data-audit.json),
[policy boundary](../prompt-injection/POLICY-CHANGES.md) and
[results](../prompt-injection/RESULTS.md).

## NotInject

**What it contains.** Benign prompts deliberately containing words or characters
that can trigger injection detectors. The [source](https://huggingface.co/datasets/leolee99/NotInject)
includes ordinary questions, technical questions, creative requests and
multilingual examples.

**Our task and use.** All examples should be ALLOW under the injection policy.
We used the original `NotInject_one`, `NotInject_two` and `NotInject_three`
splits, **113 examples each**, corresponding to one, two or three trigger words.
These are evaluation slices, not train/validation/test partitions. None supplied
policy-development examples.

This measures **false blocks and benign allow rate**, with unresolved outputs
reported separately. It cannot measure attack recall or balanced accuracy by
itself. Its multilingual examples are a small stress slice, not a broad language
benchmark. See [results](../prompt-injection/RESULTS.md#notinject-339-benign-lookalikes).

## JailbreakBench released attacks

**What it contains.** [JailbreakBench](https://jailbreakbench.github.io/) publishes
an evaluation framework and [attack artifacts](https://github.com/JailbreakBench/artifacts).
Our source is the released **attack text**, not the entire benchmark framework
or its separate benign-behavior collection.

**Our task and use.** Detect an attempted jailbreak. We used GCG adversarial-suffix
and PAIR iterative-prompt attacks targeting Vicuna-13B: **100 GCG and 82 PAIR
prompts**. Eighteen PAIR records had no released prompt and were excluded. Both
successful and unsuccessful attempts from the original attack runs are included.
No artifacts were used to author policies, and no attacks were executed.

Every retained example is a BLOCK target. We report detection rate and misses,
not balanced accuracy. **Detecting an attempt is different from preventing a
successful attack on a live application.** See the
[exact source files](../prompt-injection/preparation/source-manifest.json) and
[method-level results](../prompt-injection/RESULTS.md#jailbreakbench-182-released-attack-attempts).

## DiffusionDB and original project examples

[DiffusionDB](https://huggingface.co/datasets/poloclub/diffusiondb) contains
image-generation prompts, images and associated metadata. Our original app
browsed its **text prompts** and sent selected prompts to a policy evaluator.
It has no ground-truth labels for our custom platform rule; metadata such as an
NSFW score is not a substitute. The [demo](../../DEMO.md) is distinct from the
following scored, project-authored sets.

| Original set | Task and size | Status and source |
|---|---|---|
| Synthetic image-prompt policy showcase | A fictional platform rule about religious iconography; 24 development and 48 test cases, with ALLOW/BLOCK/REVIEW labels | [Data](../../evals/religious_iconography.jsonl), [design](../../evals/README.md), [results](../../published_runs/2026-10-21/README.md). **Not sampled from DiffusionDB.** AI-drafted labels await independent adjudication; religious expression is not being labeled inherently harmful. |
| Synthetic injection challenge | Instruction-boundary policy with REVIEW for unresolved context; 100 cases in 25 groups, split into 20 development and 80 test cases | [Data](../../evals/injection/challenge.jsonl), [methods](../../evals/injection/README.md), [results](../../published_runs/2026-10-24-injection/README.md). Agent-reviewed labels, not an independently human-adjudicated benchmark. |
| Local Ollama teaching cases | Threats versus criticism, fiction and reporting abuse; eight handwritten English cases | [Runner and cases](../../tools/ollama_policy_smoke.py), [evidence](../skill/evidence/2026-10-28/README.md). Integration check only; no held-out split or general accuracy claim. |

Serving experiments also used WildGuard text subsets and
[synthetic neutral documents of controlled length](../cloud-serving/README.md).
Those workloads measure latency, throughput and output consistency. They are
not additional labeled moderation benchmarks.

## Reproduce the population, not just the dataset name

Use each study's manifests for exact revisions, exclusions, row IDs and split
hashes. For example, the recorded WildGuardMix revision is
`d29c47f41c8b51348b5c8e8c81c039b3132b66d1`; HateXplain pins both its HF loader
and underlying GitHub data. The injection study publishes a
[source manifest](../prompt-injection/preparation/source-manifest.json) and
[checksummed evidence archive](../../published_runs/2026-11-02-prompt-injection/README.md).
Current upstream files may differ from those snapshots.

Choose a source whose labels match the intended policy, then retain separate
development and test records. Report false blocks, missed violations and
unresolved outputs alongside aggregate metrics. Combining these different
populations into one score would obscure what was tested.

PII detection, enterprise employee intent and image moderation remain outside
the completed benchmark coverage. Datasets mentioned in
[research proposals](../research-directions/README.md) are not evaluated datasets.
