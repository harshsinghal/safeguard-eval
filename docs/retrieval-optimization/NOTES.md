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

## Formatting stage completed

The registered mean over nearest-four and balanced-four validation conditions
selected labeled native-field cases for PolicyLM and Jev, and the original JSON
suffix for Shieldstral and Kev. For PolicyLM, balanced-four accuracy rose from
85.81% to 89.65%, but its unchanged policy-only control remained at 92.32%.
Jev's corresponding change was 93.88% to 93.95%, one case. The API repeat
variation above is especially relevant to interpreting such a small difference.
These are validation observations, not final test findings.

The word `native` is a configuration name for our alternate example rendering.
Both conditions use each publisher's native classification interface; none of
these comparisons establishes a publisher-endorsed few-shot format. PolicyLM's
change moves cases into different semantic policy fields. For the other models,
the same instruction field holds either JSON cases or labeled prose.

## Diagnostic checks excluded from selection

An additional validation-only diagnostic compares nearest-neighbor labels and
four-neighbor majority voting (nearest breaks ties). E5's neighbor voting scored
78.58%, Qwen 0.6B 75.46%, Qwen 4B 74.22%, and BM25 73.83%. These are descriptions
of retrieved neighborhoods, not the criterion for choosing a classifier's
retriever. A different-label example can still provide a useful contrast, and
the classifier need not copy its neighbors' labels.

PolicyLM used the same number of windows for each target in all five formatting
conditions: 1,516 validation prompts had one window, 17 had two, and one each
had three, four and six. Every condition reported one input variant. This rules
out a change in window count for this particular formatting comparison; it does
not explain the model's internal behavior. The prompt-free diagnostic script and
aggregates are retained separately from the registered selection procedure.

## Retriever stage completed

Keeping the selected layout and four-example count fixed, validation chose
Qwen3-Embedding-0.6B for PolicyLM, BM25 for Shieldstral, and E5 for Kev and Jev.
PolicyLM improved from 87.89% with E5 to 91.21% with Qwen 0.6B: false blocks fell
from 144 to 84 while misses rose from 42 to 51. Its Qwen 4B result was 90.17%.
The larger embedding model was not the winning configuration for any classifier.

Shieldstral's best retrieval accuracy was 96.81% with BM25, versus 96.61% with E5.
That small accuracy gain combined fewer false blocks (36 to 19) with more misses
(16 to 30). Jev and Kev retained E5. These choices follow the registered ordinary
accuracy objective, with balanced accuracy as a tie-breaker; they do not optimize
a deployment-specific false-block or miss-rate constraint.

The selector stage then began using these frozen choices. No final test feature
or request had been created. The previous retrieval archive's 103 checksummed
files were verified unchanged during this follow-up.

## Selection and library stages completed

PolicyLM's best retrieval candidate was the Qwen 0.6B contrast set at 92.06%
validation accuracy, below policy-only at 92.32%. One fixed set tied policy-only
on ordinary accuracy, but lost the balanced-accuracy tie-break. Shieldstral's
best retrieval candidate remained the earlier E5 balanced-four condition at
97.46%, below policy-only at 98.57%. Kev selected E5 with four diverse cases
(MMR) at 89.65%, versus policy-only at 87.96%. Jev selected E5's reranked contrast
set at 94.01%, versus policy-only at 91.67%. These are validation-selected recipes,
not test winners.

Expanding the two-example library changed validation accuracy as follows:
PolicyLM 89.52% to 88.93%; Shieldstral 97.01% to 97.33%; Kev 88.61% to 87.57%;
Jev 93.03% to 93.03%. No expanded-library condition became a final selection.
The expansion changes both eligible case length and library breadth; BM25's
corpus statistics also change. It does not isolate a pure library-size effect.

Each model had 18 distinct validation configurations, 72 in total. Intermediate
stages repeat controls and reuse exact requests; these are not independent
trials. Final ranking considered every completed configuration, not only the
latest stage. This allowed Shieldstral to return to an earlier retrieval recipe.

## Test freeze

Published [commit af5a8aa](https://github.com/harshsinghal/safeguard-eval/commit/af5a8aa)
with both intermediate selections and the final freeze before new test feature
extraction or requests. The freeze was created at 2026-11-01 20:11:32 UTC.
It chooses policy-only for PolicyLM/Shieldstral and the selected retrieval
recipes for Kev/Jev as the overall systems. Separate retrieval-only selections
are retained for all four. Test roles and aliases are fixed in `freeze.json`;
none will be replaced based on a test score.

## Completed test and interpretation

All 16 distinct frozen configurations completed the 1,699-row test population:
27,184 prediction records with no unresolved classifications. The four selected
retrieval accuracies were PolicyLM 86.52%, Shieldstral 89.94%, Kev 87.35% and Jev
89.41%. Their policy-only controls were 86.70%, 90.82%, 87.64% and 89.29%.
Overall selection retained policy-only for the two specialists; the selected
Kev and Jev recipes were kept despite their small or unfavorable test changes.

PolicyLM recovered 2.18 percentage points versus original retrieval, with a
descriptive paired interval of +0.77 to +3.65, but did not exceed its policy-only
control. Shieldstral's retrieval choice was 0.88 points below policy-only, with
an interval of -1.59 to -0.18. Kev changed by -0.29 points (-1.47 to +0.88), and
Jev by +0.12 (-0.71 to +1.00). Intervals are unadjusted and do not capture search
uncertainty, API repeat variation, or benchmark reuse.

Every selected retrieval recipe traded fewer misses for more false blocks.
For Kev, misses fell by 34 and false blocks rose by 39. Its balanced accuracy
increased from 87.31% to 87.50% while ordinary accuracy decreased. This is a
metric-dependent trade-off, not evidence that both moderation errors improved.
For Jev, 11 fewer misses and nine additional false blocks produced only two
additional correct decisions. The study supports testing the complete retrieval
configuration against a policy-only control, not a claim that more elaborate
retrieval reliably improves moderation or that retrieval cannot help elsewhere.

## Verification and controls

An independent scikit-learn 1.6.1 calculation reproduced accuracy, balanced
accuracy, macro-F1 and both error counts for all 72 validation configurations.
It also reproduced the 16 test configurations, including recall and specificity,
and confirmed the specialists' fixed output cutoffs. Results are retained in
prompt-free diagnostics alongside the final metrics.

The policy-only and original-nearest test requests exactly match the earlier
study for all models. Reused PolicyLM, Shieldstral and Jev control decisions match
that study. Kev's serial controls changed two policy-only decisions and five
original-nearest decisions relative to its earlier batched run. Its accuracy
therefore moves from 87.52% to 87.64% for policy-only and from 88.17% to 87.99%
for original nearest-four. These are execution-setting differences, not retrieval
optimization gains. Within this study all Kev conditions are serial.

## Cost and resource cleanup

The follow-up accounts for $1.821001282: $1.15 for 6,347 billed RTX6000 Ada seconds
at $0.65/hour, plus $0.671001282 in Jev accounting. The latter includes 23,786
reported requests totaling $0.668248770 and a $0.002752512 upper bound for one
lost response. No pending reservations remain. Both retrieval studies together
use $2.695934430 of the fresh $20 allowance; all studies' cumulative accounted
spending is $22.05595230256 under their separate authorizations.

All outputs were collected, the GPU terminated, temporary local/provider SSH
keys removed, and the provider listed zero active instances. RunPod was not used.
The bill includes setup, feature extraction, failures, validation and test work;
it is not a production per-request cost or latency estimate. Local electricity,
labeling and engineering time are excluded. The original frozen study remains
unchanged. Papers, articles and the versioned skill were not rewritten as part
of this experiment publication.
