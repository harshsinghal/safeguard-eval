# Do relevant labeled examples improve a fixed moderation policy?

Registered before new model classification. This is a WildGuard accuracy study;
latency benchmarking, output calibration, threshold search and weight training
are excluded. Progress and technical amendments belong in NOTES.md.

## Question

Does giving a frozen classifier examples selected for the incoming prompt improve
on its unchanged policy and on four fixed examples? Compare each model with
itself. Different native adapters are part of each system; this study does not
isolate architecture or establish that one model family is generally better.

## Models and fixed decisions

- PolicyLM 1.7B: pinned prior checkpoint and compact p4 policy, native category
  score, BLOCK at score >= 0.5. Keep native cleaning and message windows.
- Shieldstral 3B: pinned prior checkpoint and p4 policy, native Instruct/Query/
  Document format and normalized yes/no score, BLOCK at score >= 0.5.
- Kev 4B: prior pinned checkpoint, native Choice interface and released
  temperature, native argmax (ALLOW first on ties).
- Jev 1.14: OpenRouter Decisions API, require resolved version
  typesafe/jev-1.14-20261014 and TypeSafe provider, native returned choice.

Kev is selected using historical **validation accuracy at native decisions**,
not new test scores: its brief policy scored 90.625% versus Clef's best 89.0625%
on the same 512 examples. For both decision models start from their existing
brief policy, without demonstrations. All four conditions keep that model's base
policy, checkpoint and decision rule unchanged. Do not carry over any previously
optimized cutoff. PolicyLM/Shieldstral p4 policies were selected in prior studies.

## Data and retrieval

Reuse the recorded 4,096 fitting and 1,536 validation prompts from the frozen
representation studies, and all 1,699 labeled official WildGuardTest prompts
(754 harmful, 945 benign). Validate identifiers, hashes and duplicate groups.
Only prompt harmfulness is tested; responses and source-category metadata never
enter requests. The 26 unlabeled official records remain excluded as before.

The retrieval library contains fitting prompts only. Exclude empty prompts,
conflicting-label groups and examples outside 8–80 whitespace words or over 400
characters, to fit four complete examples in every model's policy budget. Retain
one deterministic representative per duplicate group. Publish actual bank counts
and exclusions. This is retrieval from an eligible subset, not unrestricted
nearest neighbors from all WildGuardTrain. Never truncate demonstration text.
Validation and test labels are unavailable to retrieval and rendering functions.

Use frozen intfloat/e5-small-v2, revision
ffb93f3bd4047442299a41ebb6fa998a38507c52, with the documented query: prefix for
symmetric similarity, attention-mask mean pooling and L2 normalization. Use
cosine similarity. Long query texts are encoded in complete nonoverlapping
500-content-token windows, with the prefix and special tokens per window; average
window vectors weighted by content-token count and normalize again. This explicit
extension avoids silently clipping long queries. Model inputs still contain the
full original query. No embedding fine-tuning or encoder search.

## Five comparisons

1. Policy only: no demonstrations.
2. Fixed four: two fitting ALLOW and two BLOCK examples selected by a fixed salted
   hash, independently of fitting errors and of evaluation queries.
3. Nearest four: four highest cosine similarities, with deterministic ID tie-breaks.
4. Balanced nearest: two nearest ALLOW and two nearest BLOCK, selected using bank
   labels only. No query label is available. Order all four by decreasing similarity.
5. Four-neighbor majority vote without a classification model, breaking a 2–2
   tie with the highest-ranked neighbor. Use the identical nearest-four bank and
   embedding method. This is one shared control, not four independent model runs.

Show every condition. Primary contrasts are nearest-four versus policy-only and
nearest-four versus fixed-four for each model. Balanced-nearest is a secondary
contrast. Validation may nominate one condition per model by accuracy, then
balanced accuracy, then fewer demonstrations, then fixed condition name order.
Freeze nominations before test; always show the full test matrix and identify
nominated conditions without replacing them by test winners.

## Model-specific rendering and compatibility

Examples are labeled data, never instructions. The base policy remains
authoritative; similarity does not imply the same decision. Only the submitted
content is classified. JSON-escape example text and delimit it from the target.
For Jev/Kev append demonstrations to question instructions; state.content contains
only the target. For Shieldstral append demonstrations in Instruct, preserve its
yes/no Query and put only the target in Document. For PolicyLM append compact
labeled illustrations to the category's exception/context text, keeping the
original rule and exceptions. This is an experimental conditioning format, not a
publisher guarantee of few-shot support.

Before validation, run fitting-only input/label-order/length checks on every arm.
Check that examples change the intended policy input, never the message being
scored. Verify native single/batched consistency where batching is used. No
example-format search based on test outcomes. If a model rejects the format or
context budget, preserve the failure and report incompatibility rather than
claiming an accuracy comparison from silently dropped examples. Technical fixes
must be documented and frozen before final scoring.

## Evaluation and interpretation

Primary metric is ordinary accuracy, as requested. Also report balanced accuracy,
false blocks out of 945 benign prompts, misses out of 754 harmful prompts,
macro-F1 and unresolved outputs. An unresolved result counts as incorrect and
never becomes ALLOW. Report corrected and introduced errors and 2,000 paired
duplicate-group bootstrap intervals for the registered accuracy differences.
Intervals are descriptive and do not correct for the many comparisons or prior
benchmark use. No threshold calibration, score fitting, or accuracy-driven
runtime tuning. Keep raw scores solely for traceability.

This is an exploratory follow-up: we have previously examined WildGuardTest.
Training labels are largely model-derived; test annotations differ. Neither
duplicate filtering nor a frozen run eliminates unknown publisher training
exposure. Gains would support this particular example library, retriever, policy
and interpreter combination, not guarantee improvement on a new policy.

## Budget, records and progress

Prior accounted spending is $19.36001787256 against the user's $20 cumulative
cap, leaving $0.63998212744. No new paid resources have been launched. The full
four-model comparison is expected to need an additional allowance; prepare the
local experiment before requesting it. Do not exceed the existing cap without
explicit user authorization. Use bounded API reservations and provider-side GPU
termination. Reconcile actual cost and verify resources have stopped billing.

Publish source, protocol, model/data hashes, retrieval IDs and similarities,
prompt-free predictions, all comparisons, limitations and CPU reproduction.
Keep dataset text, reconstructable embeddings and credentials private. Update
the main README and GitHub as part of this authorized experiment. Existing
papers, articles, skill releases and frozen studies remain unchanged.

- [ ] Verify data, adapters and prior model selection.
- [ ] Build deterministic retrieval and model-input manifests.
- [ ] Test isolation, scoring, ties, context limits and budget handling.
- [ ] Run fitting-only compatibility checks, then validation.
- [ ] Freeze nominations and implementation; run all test comparisons.
- [ ] Reproduce, publish results, and reconcile costs/termination.

Sources: [KATE](https://aclanthology.org/2022.deelio-1.10/),
[E5](https://huggingface.co/intfloat/e5-small-v2),
[WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix),
[PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b),
[Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[Kev](https://huggingface.co/jaredpalmer/kev-4b),
[Jev interface](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request).
