# Retrieval optimization research notes

## Authorization and preparation

The user authorized the proposed sequence. It continues the retrieval work
within the remaining $19.125066852 of the fresh $20 allowance. GPU.ai lists
available RTX6000 Ada capacity at $0.65/hour and no active instances. The initial
reservation is an eight-hour automatic termination limit ($5.20 maximum) and a
$2 durable Jev request cap. RunPod remains a fallback, not a second budget.

The original 1,814-group library is preserved. The separately tested expanded
library has 2,711 groups and includes every original representative. Preparation
verified the earlier data hashes and fitting/validation/test group separation.
Ten focused tests passed for exact original rendering, field semantics, escaping,
self-group exclusion, relevance gating, contrast selection, diversity and BM25.

## Fitting-bank audit

Reviewed the 24 fitting examples selected by the registered deterministic rule,
without examining new test predictions. The eligible sample includes short
ordinary requests and several context-sensitive requests involving deception,
copyright or discriminatory expression. The excluded sample includes longer
role-play frames and mixed-purpose requests where requested action and stated
purpose can pull in different directions. These are reasons to inspect context
coverage and policy boundaries; this small sample does not estimate label error
rates or establish that the length filter caused the earlier regression.

No labels were changed, no examples were removed based on this review, and no
new rules or rationales were written from test errors. Public audit metadata
contains IDs, labels, lengths and hashes only. Dataset text stays private.

## Retriever choice

Pinned Qwen3 embedding models at 0.6B and 4B and the Qwen3 0.6B reranker.
Consulted their publisher cards and current MTEB benchmark page. The latter's
text rendering returned an empty table, so no current rank is asserted. The
provider's documented English retrieval results and native instruction support
motivate this bounded comparison. E5 and BM25 are retained as controls.

PolicyLM, Shieldstral, Kev and Jev use the same revisions and base policies as
the preceding study. Earlier predictions are eligible for reuse only when the
entire request body, model revision and target identity match.
