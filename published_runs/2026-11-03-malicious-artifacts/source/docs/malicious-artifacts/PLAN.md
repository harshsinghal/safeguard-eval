# Screening malicious code and agent skills across model families

Status: authorized; prepare and register before paid inference. This is a new,
static classification study. It does not execute downloaded code, install skills,
generate malware, or test a live agent's resistance to compromise.

## Questions and scope

Can the policy, decision and general-purpose models already studied recognize
malicious software artifacts? Does a more specific policy change false blocks
and missed threats? How does a small supervised encoder compare on the same
inputs? Code-file screening and agent-skill screening are separate tasks and
leaderboards. Neither establishes that a user's request to analyze malware is
malicious, nor that an artifact can safely be executed.

The six frozen systems are **PolicyLM-1.7B, Shieldstral-1.0-3B, Qwen3.5-4B,
Kev-4B, Clef-Flash and Jev-1.14**. Add a separately trained
**LFM2.5-Encoder-350M** classifier for each task and a **character TF-IDF logistic
regression** baseline. GPT-OSS Safeguard and the other historical models are not
part of this bounded panel; family coverage is not exhaustive model coverage.

## Data and splits

**Code:** OMCBench revision `f0722971eddb654c308106c9086ff69da5b0484b` contains
800 Python/JavaScript packages and file-level labels. Read listed regular archive
members into memory only. Verify source hashes. Retain confirmed benign/malicious
UTF-8 files at least 80 characters after trimming, excluding binary, unknown,
unreadable and over-4-MiB members. Select up to two files per class per package
by a deterministic hash. This includes benign files in malicious packages.
Exclude conflicting labels for identical model views. Group files by package,
exact model view and character-five-gram cosine similarity at least 0.94, using
a fixed hashing vectorizer. Split whole connected groups: 25% test, then 25% of
remaining groups validation, using seeds 20261102 and 20261103. Within each split,
select equal classes by stable hash, capped at 1,024 fit / 256 validation / 512
test. Actual counts may be lower. This is a derived **file-level** benchmark,
not the publisher's full-package leaderboard. Labels include expert and LLM
annotations; publish their mix and all exclusion counts.

**Skills:** MaliciousSkillBench revision
`d4b42ce5766a6e0359c987cf59c1007cb3795a90`. Preserve the publisher's source-disjoint
train/validation/test allocation. Exclude five sanitized records whose original
text is withheld, if present in a partition, and the publisher's excluded rows.
Remove exact bounded-view overlaps from development in favor of test and then
validation. Select at most 1,024 fitting and 256 validation records, balanced by
class. Retain all eligible source-disjoint test records. This is text-only skill
screening; auxiliary package files are not part of the model input. Partial
attack-category mappings are descriptive slices; missing mappings are not
negative labels. Source-disjoint does not imply novel attack-family holdout.

**Common input view:** use the original text up to 8,000 UTF-8 bytes. For longer
artifacts use the first 6,000 and last 2,000 bytes, with an explicit omission
marker and UTF-8-safe boundaries. All model families receive exactly this view.
Record original hashes/lengths and clipping. Report full-view and clipped subsets
separately. Labels still describe the original artifact: missing malicious code
in the middle can limit detection, so these are results for a bounded screening
pipeline, not full-artifact inspection. No source ID, path, label, benchmark name
or package provenance is included in an inference input. Published known-data
exposure and undiscovered similarities remain limitations.

## Policy authoring and native interfaces

Freeze three candidates per task before validation: **brief**, **structured**
(concrete behaviors and legitimate-use exceptions), and **evidence** (trace the
action, target and destination; distinguish examples from active instructions).
These are prespecified variants, not training-error-derived corrections. No test
text is reviewed to author them. No retrieval or copied benchmark examples are
inserted. Select independently for each task/model by validation balanced accuracy,
then macro F1, shorter serialized policy, then policy ID. Evaluate the brief and
selected policies on test; reuse brief predictions when it was selected.

PolicyLM uses its native category/violation/non-violation/exception fields and
publisher precision preset 0.335, cleaning and native windows. Shieldstral uses
its native wrapper and yes/no next-token pair. Qwen receives the policy in a
system prompt, the artifact as JSON-quoted user data, thinking disabled, and a
yes/no classification instruction. Its next-token pair is normalized and scored
at 0.5; this is constrained label scoring, not free-form chat generation. Record
whether the unconstrained top token was a label. Kev, Clef and Jev use their native
Choice heads and argmax. Preserve publisher temperatures. No learned cutoff,
score calibration or ensemble. Run native inference serially to avoid known
batching variation. Checkpoint and adapter revisions are frozen in registration.

## Trained baselines

Each task has its own classifier trained only on that task's fitting split.
TF-IDF uses character 3–5 grams, at most 100,000 features, min_df=2, sublinear term
frequency, L2 logistic
regression, balanced class weights and C in {0.1, 1, 10}. Fit the vocabulary on
fitting data only. Select by validation balanced accuracy, macro F1, then smaller C.

Liquid uses the pinned pretrained encoder, masked mean pooling, dropout 0.1 and
a binary linear head. Fine-tune the encoder and head together, one registered
seed, AdamW at {2e-5, 5e-5}, three epochs, effective batch 32, gradient clipping 1,
10% warmup and linear decay, FP32 weights with BF16 autocast. Max 8,192 tokens;
overflow is an error rather than silent additional truncation. Select the epoch
and rate on validation balanced accuracy, macro F1, earlier epoch, smaller rate.
Use the fixed probability cutoff 0.5. This is supervised task-specific training,
not policy prompting; its label use and optimization differ from frozen models.
A single seed does not establish training stability.

Freeze every model's selection and fitted artifacts before any test inference.
Do not transfer task-specific heads between these datasets or choose a winning
checkpoint based on test. Preserve failures and any protocol amendments.

## Measures, budget and publication

Report accuracy, balanced accuracy, macro F1, MCC, malicious recall, benign
specificity, false-block and missed-threat counts/rates, and unresolved counts.
Errors stay in denominators; do not count them as successful blocks. Include
paired, grouped bootstrap intervals for policy changes, and test-set confidence
intervals clustered by package/duplicate group or skill structural family. Keep
the two tasks separate and label derived subsets clearly. Training/policy selection
and test results are distinct. Timing here is diagnostic, not a serving benchmark.

Allocate at most **$6 from the previously unused $13.151221800**, under the user's
authorization to implement this next benchmark. Reserve one GPU.ai RTX6000 Ada
at no more than $0.65/hour for at most six hours ($3.90), plus a Jev API cap of $2.
Check live pricing/balance first. GPU.ai is preferred; RunPod is a fallback within
the same cap, never an additional allowance. Use provider-side automatic
termination, collect checkpoints and predictions, reconcile billing, and verify
termination. Do not spend the remaining allowance without keeping the total cap.

Publish plan, code, source versions/hashes, prompt-free manifests/predictions,
validation selection, results, restoration instructions and cost/cleanup evidence.
Do not publish downloaded malicious artifacts, raw skill text, credentials, or
trained weights in Git. Update README, dataset/model catalogs and research log.
The papers, articles and released skill remain separate reviewed snapshots.

Sources: [OMCBench](https://github.com/False-Positive-Community/open-malicious-code-benchmark),
[MaliciousSkillBench](https://github.com/protectskills/MaliciousSkillBench),
[dataset](https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench).
