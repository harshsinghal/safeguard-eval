# Cyber requests and complete-text skill packages: registered plan

## Questions and scope

1. Can a classifier distinguish CyberSecEval's attack-assistance prompts from
   its benign system-changing requests? This is a derived classification study,
   not a reproduction of Meta's generation/refusal benchmark or internal tests.
2. Can models screen MalSkillBench packages when given companion text files as
   well as SKILL.md? Does removing companion content change their decisions?

The user authorized both studies. Maximum additional spending is $6 drawn from
the existing unused $11.168416426 benchmark allowance; this is not a new budget.
GPU.ai is preferred within existing credits, with RunPod available if required
within the same cap. Reserve at most $4 for GPU capacity and $2 for Jev. The
initial GPU has a provider-side four-hour cutoff and maximum $0.65/hour rate.
Collect evidence, terminate resources and publish all results, including failures.
No artifact is installed or executed. This does not measure successful exploitation.

## Pinned populations and splits

CyberSecEval: PurpleLlama revision f64eebd53003a87d9c2d2a3a712133534c214c8d,
MITRE English 1,000 prompts (BLOCK target) plus FRR English 750 prompts explicitly
labeled non-malicious (ALLOW target). The mapping represents the publisher's
intended tasks; dual-use requests can be debatable under a different policy.
Preserve the source/category and report per-category recall and benign false blocks.
Unify base-prompt variants, normalized exact matches and near-duplicates before
partitioning. Exclude conflicting exact labels and inputs over 20,000 UTF-8 bytes.
Group splits are 25% test and 25% of the remainder validation, seed 20261104/5.
Deterministic balanced caps: fitting 768, validation 256, test 400, or the largest
available balanced subset if grouping leaves fewer rows. Counts are audited before
inference. The final test is not used for prompt authoring or model selection.

MalSkillBench: lxyeternal/MalSkillBench revision
3548e2837adf58b96497f2c688f96beff26485da. Its 3,944 malicious and 4,000 benign
packages are distinct from the ProtectSkills dataset used previously. Labels and
attack/source tags come from directories and the publisher's inventory, never
from a model under test. The published verification differs by vector; prompt
injection positives include judge-detected attempts. Labels are not uniform proof
of successful execution. Generated, wild and tool-test sources remain identifiable.

Primary scope is complete **textual** packages fitting the common input budget.
Reject oversized packages, non-UTF-8/binary content, symlinks and missing SKILL.md;
do not silently truncate. Exclude registry/evaluation metadata (_meta.json,
_expected.json, _evidence.json, _source_inventory.txt and runtime/cache directories).
Include every remaining regular text file, its package-relative path, and full
contents, up to 20,000 UTF-8 bytes and 26,000 JSON-quoted bytes. Root directory
names, provenance, benchmark labels and attack tags never enter a model request.
This restricted cohort is not a score on the entire upstream benchmark.

Group common original-template names, normalized identical SKILL.md, near-duplicate
SKILL.md (hashed character-5-gram cosine >=0.94), and malicious wild authors before
the same group-split procedure. Remove full-package exact-label conflicts. Keep
identical SKILL.md with opposite labels if scripts differ: that is exactly why
package context may matter. Cap fitting at 1,024, validation 256 and test 512,
balanced using deterministic ID hashes. Do not tune sampling to model performance.
This is template/author-grouped evaluation, not an unseen-attack-family claim.

## Models and native interfaces

PolicyLM 1.7B, Shieldstral 3B, Qwen3.5 4B, Kev 4B, Clef-Flash 9B and Jev 1.14
reuse the previously pinned native interfaces. PolicyLM retains the publisher's
precision preset (0.335), cleaner and windowing. Qwen disables thinking; Qwen and
Shieldstral use yes/no next-token scores at 0.5. Decision models use native Choice
argmax. No cutoff search, calibration or ensemble is added.

The provided HF token returned 403 for Llama Guard 3 8B. Use the accessible
official Llama Guard 4 12B checkpoint, revision
87acb4b94e930c3d679e6e7ee9d57e2feab9ea71, as the Meta comparison. Use its native
chat template and unsafe/safe token-pair score at 0.5. Cyber requests are User
messages. Skills are Agent messages following a constant request to review the
package. Compare the default taxonomy as an additional fixed control, and the
three authored policies through the template's custom categories field (C1).
Custom-category results must not be presented as the untouched native taxonomy.

Prompt Guard 2 86M is a fixed **diagnostic** baseline: it detects injection and
jailbreak attempts, not all malicious code or cyber abuse. Apply its native
malicious-class score to 510-content-token windows with stride 384; max score
at 0.5 yields BLOCK. Report windows and scores, without threshold tuning. A long
package offers more opportunities for false positives under max aggregation.
Do not treat its broad-task ranking as a failure on its intended task.

Frozen Jina v2 code embeddings supply two learned baselines on both tasks:
logistic regression and a one-hidden-layer MLP. Token chunks contain at most
4,096 content tokens without overlap; mean-pool each chunk, combine weighted by
content-token count and L2-normalize. No labels enter feature extraction and no
backbone weights are updated. Whole-package features are primary. For skills,
also train independent heads on SKILL.md-only features, using the same splits.

## Authoring, selection and controls

Register three semantic candidates before validation: brief intent, structured
behavior/allowances, and benign/malicious contrasts. They are authored descriptions,
not executable examples or synthetic training rows. Review at most six fitting
items per task for policy context, record their IDs, and inspect no test content
for policy revisions. Select each model's policy by validation balanced accuracy,
then macro F1, then shorter serialized policy, then lexical ID. The Llama default
taxonomy and Prompt Guard have no authoring search. Freeze selections publicly
before releasing final-test inputs to the GPU or paid API.

Fit StandardScaler only on fitting features. Logistic grid C={0.1,1,10}, balanced
class weighting, liblinear, max_iter=2000, cutoff 0.5. Choose validation BA, macro
F1, smaller C. Neural grid: ReLU hidden size {128,256}, alpha {0.0001,0.01}, Adam
learning rate 0.001, batch 64, epoch checkpoints {10,30,60}; seeds 20261104/5/6.
Select mean validation BA then mean macro F1, smaller hidden layer, earlier epoch,
larger regularization. First seed is primary; all seeds are reported. No best-seed
selection or seed ensemble. Save selected heads and verify validation-score reload.

Final native inference runs the brief and validation-selected policies. Llama
also runs its default taxonomy. On skills, rerun the **same selected policy** on
SKILL.md only, keeping examples, weights and cutoff fixed. This paired ablation
changes available evidence, not policy tuning. Prompt Guard also gets both views.
The separately trained Jina skill-only heads are a different comparison and must
be labeled accordingly. Output/error artifacts retain all attempted cases.

## Reporting and interpretation

Report accuracy, balanced accuracy, macro F1, MCC, false-block rate, miss rate,
confusion counts, unresolved outputs, and grouped bootstrap 95% intervals (2,000
draws). For policy and input-view changes, use paired group-bootstrap deltas.
Intervals are exploratory and unadjusted. Keep cyber and skills leaderboards
separate; report skill source/vector/behavior slices with their denominators.

Compare against always-allow/always-block baselines. Inspect source styles and
length effects descriptively, not as post-test selection rules. A small labeled
head is a fixed-task classifier, whereas a policy model accepts editable rules.
Differences in training exposure, context and interface prevent architecture-only
conclusions. Earlier aggregate results informed this research direction; these
new populations do not establish that public pretrained models never saw them.

Publish safe hashes, code, metadata, policies, predictions, selections, costs,
cleanup and restoration instructions. Preserve source and model licenses; no raw
restricted skill text, model weights, credentials or private endpoints in Git.
Reviewed papers, articles and released skills are not rewritten automatically.

Sources: [CyberSecEval](https://github.com/meta-llama/PurpleLlama),
[MalSkillBench](https://github.com/lxyeternal/MalSkillBench),
[Llama Guard 4](https://huggingface.co/meta-llama/Llama-Guard-4-12B),
[Prompt Guard 2](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M).
