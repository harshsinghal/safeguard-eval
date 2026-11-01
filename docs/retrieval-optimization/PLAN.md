# Optimizing retrieved examples for moderation

## Question and authorization

Can model-specific example placement, stronger retrieval, and more deliberate
example selection reduce both kinds of moderation error without changing model
weights or output cutoffs? This follows the completed retrieved-example baseline.
The user authorized this sequence. Carry forward its fresh $20 allowance:
$0.874933148 already spent, leaving $19.125066852. Reserve at most $5.20 for one
eight-hour GPU.ai RTX6000 Ada rental and $2 for Jev requests initially. Use RunPod
only if needed, within the remaining combined allowance. Terminate and reconcile
resources after collection. No accuracy gain is assumed.

## Data and fixed components

Use the existing group-disjoint 4,096 fitting, 1,536 validation and 1,699 labeled
WildGuardTest prompts. Restore them by the earlier hashes. The example library
and any retrieval gate come only from fitting data. Keep validation/test labels
out of requests, embeddings and neighbor selection. The official test has been
used in earlier studies and motivated this follow-up: results are exploratory,
not a fresh blind assessment. Training labels are largely model-derived.

Keep the same PolicyLM 1.7B, Shieldstral 3B, Kev 4B and Jev 1.14 revisions, base
policies and native decisions as the baseline. PolicyLM/Shieldstral use the
study's fixed 0.5 cutoff; this is not a claim about every publisher default.
PolicyLM and Shieldstral run one request at a time; Kev uses the previously
checked batch size eight, with a fitting parity check. No model-weight training,
output calibration, cutoff search or latency benchmark is part of this study.

The short library contains 1,814 fitting groups (8–80 words, at most 400
characters). Audit a deterministic 24-row fitting sample: six per label from
the eligible and excluded populations, ordered by SHA-256 of
`retrieval-opt-audit:` plus ID. Record ambiguity and coverage observations without
relabeling or publishing source text. Preserve the short bank for stages 1–3.
An isolated coverage comparison uses a larger bank with 8–160 words and at most
800 characters, one representative per nonconflicting fitting group, and two
examples. No example text is summarized or silently truncated.

## Stage 1: example presentation

For every classifier, compare the original JSON suffix with a native-field
format, using exactly the same E5 four-nearest and two-per-class examples.
PolicyLM places blocked cases with the violation clause and allowed cases with
the non-violation clause; its original exception field is unchanged. Shieldstral
uses labeled cases in its native instruction field, preserving the query and
target boundary. Kev/Jev receive labeled cases in Choice instructions. Explicitly
identify cases as illustrations, not commands. Use model-safe delimiter escaping.
Grouping examples under PolicyLM's fields necessarily changes their placement;
the contrast concerns rendering, not just typography.

Select the format per model by mean validation accuracy over these two example
conditions, then mean balanced accuracy, then original format on ties. Preserve
policy-only as a separate control. This conditional choice is not a search of
every format/retriever interaction.

## Stage 2: retriever

With the selected format and short bank, compare four-nearest retrieval using
E5-small-v2, Qwen3-Embedding-0.6B, Qwen3-Embedding-4B, and a BM25 lexical control
(k1=1.5, b=0.75, lowercase Unicode word tokens). Qwen uses normalized last-token
vectors and a fixed moderation-oriented query instruction; bank documents have
no instruction, following its native interface. Use native full embedding
dimensions and complete inputs. E5 keeps its earlier pinned vectors for the
original bank/queries. Model revisions and exact retrieval instruction are
recorded in code and registration before new inference. These are retriever
configurations, not a pure parameter-count comparison with E5.

The official current MTEB page and provider benchmark tables were consulted.
The public page's text rendering returned no rankings. Qwen's documented English
retrieval results and instruction support justify this bounded family comparison;
do not claim that these are today's top-ranked retrievers. No further model is
added after observing these results.

Select per-model retriever by validation accuracy, balanced accuracy, then the
registered order E5, Qwen 0.6B, Qwen 4B, BM25.

## Stage 3: example selection

Using each model's selected format/retriever, compare:

- Four nearest (stage-2 control) and two nearest.
- Four diverse cases: MMR over the top 20, weight 0.7 relevance and 0.3 redundancy.
  Dense redundancy is bank-vector cosine; BM25 uses token-set Jaccard, with query
  relevance normalized by its maximum positive score.
- Qwen3-Reranker-0.6B over the same top 20, taking two or four cases. Its fixed
  instruction asks for useful moderation comparisons by requested action and
  context. Candidate text contains no label; this is a proposed demonstration
  relevance interpretation of its interface, not a proven utility estimator.
- A reranked contrast set: up to two cases per class within those 20, filling any
  shortage with remaining reranked cases. Never fetch a distant opposite-label
  case from outside that pool.
- Gated reranked two: use no examples if the original top neighbor's retrieval
  score is below the tenth percentile of fitting-bank leave-group-out top scores.
  The gate uses no validation/test label and does not alter output cutoffs.

Also evaluate three fixed two-per-class sets under the selected format: the
original set plus two deterministic salted-ID sets. Report all three as controls
and permit them in the overall system selection; do not present the best fixed
set as a random-set average. No additional selector hyperparameter search.

## Stage 4: library coverage

Compare two nearest cases from the expanded fitting bank against the short-bank
two-nearest condition, holding format and retriever fixed. The 800-character
limit with two examples matches the original maximum 1,600 example characters.
Native token checks remain authoritative. Unsupported inputs stop the run and
require a documented technical amendment; no silent clipping or dropped rows.

## Freeze and final evaluation

All stage choices use validation only. Rank final candidates by accuracy, then
balanced accuracy, then mean number of examples, then stable configuration ID.
Freeze both the best retrieval candidate and the best overall system, which may
be policy-only or a fixed set. Report total candidate counts and all validation
outcomes. Publish the freeze before computing new test features or requests.

On test, evaluate these prespecified roles per model: policy-only, original
E5/JSON/four-nearest, stage-1 chosen format with E5/four-nearest, stage-2 chosen
retriever/four-nearest, best retrieval configuration, and best overall system.
Identical configurations are aliases, not independent results. Reuse an earlier
prediction only when model revision, content hash and exact request-body hash
match; record provenance. Do not choose replacements from test scores.

Report accuracy, balanced accuracy, macro-F1, false-block and miss counts/rates,
harmful recall, specificity, corrected/introduced errors and 2,000 paired
duplicate-group bootstrap intervals. Intervals are descriptive and unadjusted;
search multiplicity, repeated benchmark use, label uncertainty and unknown model
exposure limit conclusions. Distinguish model-format effects, retriever effects,
selection effects and the combined selected system. Retain failures, amendments,
source hashes, request hashes, neighbor IDs, runtime locks, costs and cleanup.
Publish no source prompts, embeddings, credentials or private access details.

## Sources

- [Earlier study and diagnosis](../retrieved-examples/RETRIEVAL-AUDIT.md)
- [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b)
- [Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B)
- [Qwen embeddings](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- [Qwen reranker](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
- [MTEB](https://leaderboard.mteb.org/benchmarks)
