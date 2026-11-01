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

## Provisioning and runtime

The provider accepted the instance creation and returned `operation_id`. The
reused launcher expected `id` and stopped at its local acknowledgement check.
Recovered the accepted operation and its instance rather than submitting a
second creation. The server reports an eight-hour automatic termination time.
This is a provisioning compatibility issue, not an inference or selection change.

Both environments installed successfully. Embedding extraction and development
retrieval began with no validation/test labels in query inputs. The original
test inputs and vectors have not been uploaded to the development GPU.

## Exact-request cache variation amendment

The first Jev smoke attempt stopped before sending new requests because its
cache integrity check found varying earlier responses to identical inputs.
Across 247 duplicate requests in the earlier fitting-smoke/validation cache,
Jev had 111 score differences above 0.000001, a maximum difference of 0.07, and
four decision differences. The other three models had no differences in those
duplicates. This is a cache-repeat diagnostic, not a representative reliability
estimate or a new accuracy result.

Before Jev inference or any stage selection, change the cache rule to retain
the first response in sorted source-file and original line order. Prior cache
files precede newly generated files; their recorded order places nearest-four
before balanced-nearest when requests coincide. No target label or correctness
is used. Preserve every prior response and record discrepant duplicate IDs and
decisions in runtime diagnostics. Identical new requests share one response.
Consequently an original balanced condition can differ from the earlier study
when its request was repeated there with a different API answer; the original
nearest-condition control retains its earlier response.

PolicyLM smoke and part of its validation execution had begun under the first
registration. Their duplicate responses were identical, and this cache change
does not alter their inputs, decisions or selection rules. Keep those results,
the failed Jev attempt and the original source/registration. Update the source
hashes before further stages; no native run is repeated to improve a result.

## Transport failure and bounded retries

A Jev validation request lost its response after 2,380 successful smoke/validation
requests had been billed. Preserve those responses and partial predictions. Count
the missing response at its full $0.002752512 reservation, an upper bound rather
than a known billed amount. Before resuming, register at most three separately
reserved attempts per request for transport failures and retryable HTTP statuses.
Use the first successful response; never retry because of its classification.
Invalid pricing or an unresolved reservation still stops the run. The $2 API cap
is unchanged. Unit checks cover unknown-charge accounting and stop-on-invalid-bill.

## Kev batch parity amendment

The new fitting-only format check found a maximum score difference of
0.0063854456 between batch eight and serial inference, exceeding the registered
0.005 tolerance, with zero decisions changed across 16 examples. Before any new
Kev validation classification, switch Kev to batch one for this study. Preserve
the rejected parity record and partial smoke file, which contained only cached
older predictions.

Disable the earlier batch-eight Kev cache and recompute its controls serially
alongside every new condition, including final test controls. Reuse only new
serial results for identical requests. This keeps within-study comparisons at
the same execution setting. It may produce a slightly different baseline than
the preceding study; report the new control and do not attribute cross-study
numerical differences to policy or retrieval. Other models' runtimes and caches
are unchanged. No output cutoff or selection rule is altered.
