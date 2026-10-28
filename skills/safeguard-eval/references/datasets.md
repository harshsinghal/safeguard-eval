# The datasets: what they can and cannot tell us

Use this guide when someone asks what to learn from, download, or benchmark.
Repository source IDs resolve through [sources.json](sources.json). Upstream links
describe the publishers' datasets; the pinned manifests describe our actual use.
Do not assume the current dataset revision matches the experiment snapshot.

## The inventory

| Dataset or set | Role in this project | What was classified |
|---|---|---|
| [WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix) | Main policy search, generalist comparison, transfer, and ensembles | Whether a user prompt requests harmful assistance |
| [HateXplain](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain) | Main policy component, presentation, transfer, and ensemble studies | Hate speech versus offensive or normal text |
| [Deepset prompt injections](https://huggingface.co/datasets/deepset/prompt-injections) | Earlier detection demonstration | Agreement with its binary injection labels |
| Original synthetic injection challenge | Earlier, separate demonstration | ALLOW/BLOCK/REVIEW under an instruction-boundary policy |
| [DiffusionDB](https://huggingface.co/datasets/poloclub/diffusiondb) | Original interactive image-prompt browsing demo | Text prompts evaluated against a chosen example policy |
| Original synthetic image-prompt set | Earlier scored comparison; **not sampled from DiffusionDB** | ALLOW/BLOCK/REVIEW under a fictional iconography rule |

WildGuard and HateXplain provide the main evidence for policy authoring. The
smaller demonstrations have different methods and weaker label validation. Do
not combine them into one headline score or imply that we evaluated images.

## WildGuardMix: harmful requests, not every moderation task

The publisher supplies `wildguardtrain` and `wildguardtest` configurations and
labels for prompt harmfulness, response harmfulness, and refusal. Our task used
**prompt harmfulness only**: harmful → BLOCK, benign → ALLOW. The model saw the
user prompt, not the assistant response, gold label, or gold risk category.

Our recorded dataset revision is
`d29c47f41c8b51348b5c8e8c81c039b3132b66d1`. The importer retained 86,759 training
rows and grouped exact/approximate near duplicates before creating internal
fitting, validation, and audit partitions. The original policy search used
**1,024 fitting, 512 validation, and 512 audit examples**, not the full training
set. An expanded fitting estimate used 8,192 rows. The official test contained
1,725 rows; we retained **1,699** with a prompt-harmfulness label and excluded 26
unlabelled rows. The retained test has 754 harmful and 945 benign prompts.

Training examples informed revisions; validation selected policies and decision
settings; the first official test was opened after those choices were frozen.
This was testing on new examples from related categories, **not an unseen-category
experiment**. Later studies reused that test, so they are exploratory extensions,
not repeated independent confirmations. The training and test annotations also
have different origins: GPT-4-assisted training labels versus human test labels.

The [WildGuard paper](https://arxiv.org/abs/2406.18495) explains the upstream task.
Our exact construction and protocol are `wildguard-data`, `wildguard-methods`,
`wildguard-results`, and `wildguard-official-source`. The test manifest is in the
frozen run archive. Public prediction records omit gated prompt text. Follow the
dataset's current access terms if reproducing inference.

Exposure is a separate concern from our split separation. WildGuard was trained
upstream for this task, and other models may have encountered public benchmarks.
PolicyLM discloses a training source containing WildGuardMix; exact overlap is
unverified. See `model-exposure`. Do not describe all checkpoints as benchmark-naive.

## HateXplain: hate is not the same as all offensive speech

The [dataset project](https://github.com/hate-alert/HateXplain) and
[paper](https://arxiv.org/abs/2012.10289) provide hate/offensive/normal annotations,
target information, and rationales. We took the majority class and mapped
**hate → BLOCK; offensive and normal → ALLOW**. This deliberate binary mapping
does not reproduce the full three-class benchmark or validate rationale extraction.
An organization's policy might draw a different boundary.

The original split counts are 15,383 training, 1,922 validation, and 1,924 test
posts. After approximate duplicate-group quarantine, our structure study used
**1,024 fitting, 1,920 validation, and all 1,924 test posts**. Four demonstration
examples came only from training; their groups were excluded from fitting.
The test contains 594 hate, 548 offensive, and 782 normal posts. Model input was
the publisher's tokens joined with spaces; annotator votes and rationales were
not supplied as hidden hints.

The HF loader was pinned at `f6a8b7de6ec31b30919d2f48cf685400ce61185f` and the
underlying `hate-alert/HateXplain` files at
`01d742279dac941981f53806154481c0e15ee686`. See `hatexplain-data`, `hatexplain-plan`,
and `hatexplain-results`. The distinct pins matter because a loader and its
upstream data can change independently.

This dataset helps study the boundary between identity-based hate and other
offensive expression. Label disagreement, missing conversational context, and
unknown upstream training exposure limit conclusions. A better aggregate score
can still mean more missed hate cases; report false blocks and missed hate too.
It does not establish fairness across all groups, languages, or deployments.

## Later ensembles reused these tasks

The ensemble stage used **4,096 fitting and 1,536 validation examples per task**,
excluding groups used for earlier policy development. WildGuard development came
from eligible rows in the previously scored 8,192-row population; HateXplain used
fresh eligible training groups. Official tests stayed at 1,699 and 1,924 rows.
See `ensemble-data`, `ensemble-archive`, and `logits-plan`.

These are new development cohorts, not new independent test datasets. The policy
texts and language-model weights stayed fixed; labelled development data fitted
calibrators and supervised combiners. The log-odds extension reused these saved
scores, development splits, and tests. Its gains are not additional policy edits.

## Deepset and the separate injection challenge

Deepset's original 546 training and 116 test examples were pinned at
`4f61ecb038e9c3fb77e21034b22511b523772cdd`. Five near-duplicate training rows were
removed, leaving **541 development and 116 test rows**. Development was used only
for threshold calibration, not language-model training. Original binary labels
were retained even where the missing application context made them debatable.
Thus the score measures dataset agreement, not exact fidelity to our written rule
or a downstream assistant's resistance to attack. Related translations/templates
also weaken an independence assumption in row-based confidence intervals.

The separate synthetic challenge has **100 cases in 25 scenario groups**: 20
development cases and 80 test cases. It adds REVIEW for unresolved trust context.
Labels were drafted/reviewed by an agent, not independently adjudicated by people.
Its regular construction and small multilingual contrasts are not evidence of
natural ambiguity coverage or multilingual performance. Report the two tracks
separately. Score-band abstention is not the same as understanding uncertainty.

See `injection-methods`, `injection-provenance`, and `injection-results`. The
recorded Deepset card had conflicting license metadata (Apache-2.0 and CC-BY-4.0).
We did not resolve that discrepancy; check the publisher before redistribution.

## DiffusionDB and the first synthetic demonstration

DiffusionDB supplies image-generation prompts and metadata. It supported the
original browsing demo. Its prompts are not labelled for our custom platform
policy; a generic NSFW score cannot stand in for that label. For text-only work,
start with the prompt metadata rather than downloading the image corpus.

The scored iconography demonstration instead used **72 original synthetic cases**:
24 development and 48 test, with 16 test examples per ALLOW/BLOCK/REVIEW class.
Those labels await independent human adjudication. The rule was a fictional
platform restriction, not a claim that religious expression is harmful. No
generated images were evaluated. See `demo-methods` and `early-demo`.

## Choosing a new benchmark

Match the intended decision to the annotation instructions before choosing the
dataset. Check splits, duplicate groups, languages, label provenance, licenses,
and whether the policy itself is supplied or must be reconstructed. Keep category
definitions separate from the model's answer format. Reserve a fresh test for
confirmation when earlier tests have influenced research choices.

PII, enterprise employee intent, multilingual deployment, and image moderation
are not validated extensions of these main studies. Datasets discussed as ideas
are not completed experiments. Use [search guidance](search.md) to locate suitable
primary sources, and label any new benchmark or policy mapping as a proposal.
