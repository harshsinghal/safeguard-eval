# Evidence supplied to an enterprise policy model

## Registered preparation

This phase produces the schema, a fixed pilot policy, 200 selected inputs, blank
annotation records, and a local review interface. It precedes teacher annotation,
training and moderation inference. Owner instruction keeps this work local.

Select 12 cases per task from the existing 14-task evaluation inventory, six per
new split. Add 16 authored pairs, with eight whole pairs per split. Each split has
100 prompts. Keep complete source text. Original benchmark decisions are sampling
metadata only and must be hidden from annotation and inference views.

Use source group IDs and normalized exact duplicates as grouping constraints.
Additionally connect texts with at least 0.80 Jaccard similarity on normalized
five-word shingles. Connected components stay in one split. Assign components
by SHA256 of `evidence-v1:` plus their lowest source group ID, modulo two.
Within each task/split, round-robin sorted original decision/length-band strata,
sorting candidates by seeded SHA256 of their ID. Select at most one member of
each connected component per task/split. Fail visibly if quotas cannot be met.
Exclude the previous 30 source cases in the Qwen graph pilot.

This is a new experiment split of previously studied data. Prior models and
researchers have seen this source suite. Similarity screening cannot identify
every paraphrase or shared template. Source group IDs and overlap checks are
recorded. Source labels must be re-adjudicated under this pilot policy.

Authored pairs are diagnostic controls. Pair members share a group and remain
together. Coverage includes quoted requests, negation, authorization claims,
credential reference/value distinction, action order, code, tool messages and
long irrelevant context. Their intended contrasts are hypotheses until review.

The schema keeps the 12 existing entity types and nine action types. Add explicit
software-agent, location and general-group types to cover documented pilot gaps.
Action, purpose, authorization and condition spans are separately typed mentions.
Missing and ambiguous information is recorded. Empty annotations start pending,
never as negative gold. Exact Unicode offsets are end-exclusive.

## Subsequent experiment, pending annotation

Review development annotations and freeze training choices using development
only. Independently human-review evaluation annotations before accuracy claims.
The first policy-model comparison uses original text, evidence with source
excerpts, and original text plus evidence. Keep the same policy/model/decoding
across conditions. First compare reviewed evidence, then predicted evidence.
Measure missed violations, false alarms, REVIEW/invalid coverage, latency, span
and role accuracy, and scope/negation preservation. Choose model, thresholds,
input limits, metrics and stopping rules in a new registration before inference.
Revisit specialization after measuring evidence quality with one policy model.

## Provenance and verification

Store full source text and review files in ignored `work/evidence-moderation-v1`.
Export IDs, hashes, counts, grouping and status under `local_runs`. Record code,
schema, policy, source inventory and private input hashes. Verify 200 unique cases,
100 per split, group and duplicate separation, quotas, exact source binding,
annotation validation and absence of restricted text in safe evidence. No GPU
worker or paid API is needed for this preparation.
