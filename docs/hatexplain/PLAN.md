# Structured policy authoring and transfer on HateXplain

Prospective protocol, 26 October 2026. The user authorized implementation. This
study tests how policy wording and presentation affect governance decisions with
fixed models, and how selected wording transfers through native interfaces.

## Task, data, and scope

BLOCK the publisher's majority-labelled hate speech. ALLOW offensive-but-not-hateful
and normal posts. This is a binary mapping of a three-class benchmark, not a general
toxicity detector or a validated ALLOW/BLOCK/REVIEW workflow. REVIEW is not a gold
label in this study. The policy is our operational formulation grounded in the
publisher's paper, annotation interface, and training data; it is not an official
verbatim HateXplain policy.

Pin the Hugging Face loader and its upstream GitHub dataset and split manifest.
Reconstruct text by joining the original post tokens with spaces. Use the original
three-class majority vote; do not merge votes into binary classes before voting.
Rows outside the official split manifest are not silently added. Preserve all
1,924 official test rows. Detect exact and approximate near-duplicate components
before modelling and remove overlapping development rows, prioritizing test over
validation over training. The data manifest records the grouping algorithm,
quarantined IDs, source hashes, and counts. This audit is mechanical; test examples,
individual labels, and errors are not authoring feedback.

Use 1,024 proportionally stratified training posts for fitting feedback, 1,920
remaining validation posts for selection, and the complete test for final reporting.
Four short unanimous training examples are selected by a fixed hash rule, before
inference: two hate, one offensive, one normal. Their duplicate groups are excluded
from fitting feedback. Keep those same demonstrations in all applicable conditions.
Target labels, rationales, and annotator judgments are not classifier inputs.

## Models and interfaces

Use pinned PolicyLM 1.7B, Shieldstral 3B, and Qwen3.5-4B checkpoints from the earlier
study. The registry records revisions. No weight updates. PolicyLM uses one hate
category with its native violation, non-violation, and exception fields. The mapping
includes every active component. Shieldstral retains its fixed system instruction
and instruction/query/document wrapper. Qwen receives a system policy and separate
submitted post, with thinking disabled and strict freely generated A/B output.

Use bfloat16, temperature zero, HTTP concurrency 32, no inference retries, and
fixed 0.5 score cutoffs for specialists. Preserve PolicyLM's native cleaner and
windowing, disable its character cap, and set max_batch_rows=1. Cutoff tuning is
not part of the primary text comparisons. Report this choice rather than claiming
it is each model's optimal operating point. Qwen's native A/B answer is primary.
Validate policy length through the pinned native helper and record full-prompt
token counts for chat models. Never silently truncate. Record maximum-length
settings and exact runtime environments.

## Registered comparisons

1. **Common complete policy.** A structured source with scope, definitions, BLOCK
   rules, ALLOW rules, exceptions/precedence, and four labelled demonstrations.
   Native fields for PolicyLM; Markdown body for Shieldstral and Qwen.
2. **Presentation.** Shieldstral and Qwen each receive linear, Markdown, tagged,
   and reordered Markdown versions. Clause text is byte-identical. Tagged means
   XML-style delimiters, not XML parsing. Linear/Markdown/tagged compare layout;
   reordered Markdown separately changes order. PolicyLM is excluded because its
   field adapter would erase a whole-document format treatment.
3. **Components.** For every model compare the complete reference with four
   individual omissions: definitions; exception/priority section; ALLOW examples;
   all examples. Hold gold labels and intended requirements fixed. These remove
   information and change length; they are not pure formatting tests. Related
   concepts may remain elsewhere. Never recommend an incomplete policy solely
   because its score is higher.
4. **Bounded wording revision.** Two rounds per recipient, plus unchanged p0.
   A single pinned Qwen-4B editor receives that recipient's fixed interface guidance,
   current policy, and up to 24 fitting errors plus eight correct fitting cases.
   Feedback is balanced across error/class strata and deterministically sampled.
   Each call has a fresh context and receives no other recipient's results,
   validation errors, or test information. Round two uses round one's fitting
   feedback. Keep scope, demonstration texts, schema, and clause IDs fixed. Only
   definitions, BLOCK rules, ALLOW rules, and exceptions may be reworded. Policies
   are capped at 650 words and the native model's token budget. Two revision
   attempts per model; invalid outputs remain recorded, with no uncounted retries.
   The coordinating assistant reviews scope before validation: this is AI-assisted
   review, not independent human adjudication. Rejected revisions cannot win.
5. **Selection and transfer.** Select among eligible p0/p1/p2 using validation
   binary macro-F1, then accuracy, shorter text, and policy ID. A model may retain
   p0. Transfer each source winner's substantive clauses unchanged to all three
   recipients using the fixed native renderers; no recipient-side rewriting or
   selection. Deduplicate identical conditions and report the resulting matrix.

Freeze all policies, eligibility reviews, source selections, adapters, and final
run matrix before uploading test inputs to the GPU. Evaluate all registered
presentation and omission conditions, not just favourable ones. The default
renderer is fixed, not selected on validation. The full matrix has at most 30
distinct test conditions: three references, six other formats, twelve omissions,
and nine selected-policy transfers. Some transfer cells reuse the reference.

Repeat each reference on a prespecified stratified 256-test-post subset to describe
inference variability. This is a repeated measurement after freeze, not a new policy
search. Optional role/persona ablation, a second example set, and repeated optimizer
seeds are deferred to keep this execution bounded; no variance across searches is
claimed from this single two-round search.

## Metrics and interpretation

Primary selection objective: binary macro-F1. An ERROR is incorrect and is mapped
to the opposite gold class for this conservative F1 computation; preserve ERROR in
saved predictions and report it separately. Show accuracy, hate recall and missed
hate, false blocks of offensive posts, false blocks of normal posts, and cases fixed
and newly broken. Report agreement/platform slices and descriptive target slices
with at least 30 posts. Target groups overlap; these are not causal fairness tests.

Compute paired 95% intervals for accuracy and macro-F1 differences using 2,000
bootstrap samples of duplicate components. Predeclare source-selected versus p0,
each presentation/omission versus its reference, and transferred versus p0/recipient
winner contrasts. Intervals are descriptive and unadjusted for multiple comparisons;
do not claim significance from a favourable cell or an exhaustive optimal model.

The practical question is how much performance and which error types change when
one maintained policy is used across models versus model-specific wording. Scope
preservation and whether the intended treatment actually reaches each model must
be checked alongside scores. Public benchmark exposure in upstream model training
is unknown. This study cannot establish universal portability or intrinsic model
superiority.

## Budget and progress records

Prior cumulative project spending: $10.78119753456. Existing cumulative cap: $20.
GPU.ai has credit and suitable capacity; RunPod remains the fallback under the
same cap. Plan at most one three-hour rental at $1.99/hour with zero disk charge,
provider-side automatic termination, and continuous artifact collection. Maximum
planned new compute: $5.97, leaving additional headroom. Provision only after local
runner checks and protocol registration. Terminate promptly and reconcile actual
billing; do not equate account credit with spending authorization.

Preserve protocol/source hashes, failed attempts, exact policies and diffs,
component mappings, rendered requests, checkpoint/environment identities,
selection/freeze records, row-level predictions and metrics. Raw data and traces
stay in the local private work directory; public evidence can use IDs and hashes.
Update the lab notebook and progress file. Produce a readable findings note,
supporting tables/figures, and CPU-only reproduction, without automatically rewriting
the existing paper before the new evidence is assessed.

Sources: [Hugging Face dataset](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain),
[publisher repository](https://github.com/hate-alert/HateXplain),
[paper](https://arxiv.org/abs/2012.10289), and the
[native-interface audit](../research-directions/POLICY-INTERFACE-AUDIT.md).
