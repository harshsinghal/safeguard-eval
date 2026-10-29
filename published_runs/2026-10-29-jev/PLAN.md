# Jev on the existing WildGuard and HateXplain tasks

Registered before benchmark inference, 29 October 2026. This bounded extension
tests a decision-model API on the same binary tasks and official test populations
as the earlier Safeguard Eval studies. It does not test a claim about human
“System 1” cognition or isolate an architecture's causal effect.

## Questions

1. What accuracy, macro-F1, missed violations, and false blocks does Jev achieve?
2. Does adding policy detail or training-derived examples improve its outcomes?
3. Does validation-only threshold selection help beyond changing the policy?
4. How do these complete configurations compare with frozen earlier results?

The expected answer is unknown. Valid typed output does not establish correct
classification. No model-weight updates, GPU rentals, or new ensemble fitting.

## Model and native interface

Use OpenRouter's Decisions API, `POST https://openrouter.ai/api/alpha/decisions`,
with `typesafe/jev-1.14`. The synthetic connectivity check resolved it to
`typesafe/jev-1.14-20261014`, served by TypeSafe. Require that resolved identity
on every benchmark response; stop on an unexpected model or provider. Do not use
`typesafe/jev-router`, which routes to other models, or a moving latest alias.

Place only the submitted text in `state.content`. Use Choice questions with
`instructions` and `criteria` for ALLOW/BLOCK. Store both option probabilities,
the native choice, confidence, model/provider, request hash, usage, latency, and
errors. The BLOCK probability is the classification score. Never send dataset
labels, row IDs, categories, or split information as model inputs.

Questions for different policy variants may share a request for the same content;
the provider documents independent evaluation against the same state. Never put
multiple dataset examples into one state. Report cost and latency per request,
including its question count; these are not comparable single-policy serving
benchmarks against the earlier GPU deployments.

## Data and labels

Reuse the exact local files and verify their SHA-256 hashes before any request.
Verify ID, text-hash, and duplicate-group separation between development and test.

| Task | Fitting | Validation | Official test |
|---|---:|---:|---:|
| WildGuard prompt harmfulness | 1,024 | 512 | 1,699 |
| HateXplain hate versus non-hate | 1,024 | 1,920 | 1,924 |

WildGuard uses the published prompt-harmfulness target, not response harmfulness
or refusal detection. Harmful requests map to BLOCK and benign requests to ALLOW.
HateXplain uses the earlier binary mapping: majority hatespeech → BLOCK;
offensive and normal → ALLOW. This mapping is not a recommendation to allow
offensive content on every platform. Neither task supplies a REVIEW ground truth.
No test labels or test errors inform wording or thresholds. These public tests
have been used in earlier studies, so this extension is exploratory rather than
a fresh, blinded confirmation. Model training exposure is unknown.

## Bounded policy search

- **brief:** concise task instructions and class definitions, without examples.
- **detailed:** reuse the original baseline policy's definitions, conditions, and
  exceptions through Jev's native instructions/criteria. Omit its old examples.
- **examples:** the identical detailed policy plus four labeled fitting examples.
  Select two BLOCK and two ALLOW cases from detailed-policy fitting errors when
  available, with distinct duplicate groups, 8–100 words, and at most 800
  characters. Prefer three-annotator agreement when that metadata exists. Within
  each tier sort by a fixed SHA-256 salt and ID. If a label has insufficient error
  cases, fill from correct fitting cases under the same constraints. Never use
  validation/test examples or rewrite the chosen texts.

First evaluate brief and detailed on fitting data. Construct the examples variant
by the registered rule; record the chosen IDs, labels, text hashes, and provenance.
Freeze all three policies before validation. No open-ended revision loop or
additional candidate is permitted after looking at validation or test results.

Select the policy with highest validation accuracy at native Choice argmax,
breaking ties by macro-F1, then fewer serialized question bytes, then policy ID.
Tune a decision threshold separately for (a) that policy and (b) the brief control
using only validation. Search 0.00–1.00 in 0.01 increments plus 1.000000001
(all ALLOW); classify BLOCK when score >= threshold. Break threshold ties by
accuracy, macro-F1, distance to 0.5, then lower threshold. Keep native Choice
decisions as the default baseline, including the provider's tie behavior.

Freeze selections, thresholds, policy hashes, dataset hashes, and implementation
hashes for both tasks before test inference. Report brief/default,
brief/calibrated, selected/default, and selected/calibrated; preserve all three
policies' default test results as descriptive results, not new selections.

## Reporting and comparison

Report accuracy, macro-F1, BLOCK precision/recall/F1, confusion counts, failed
responses, Brier score and log loss for complete valid score populations. Errors
stay in the evaluation denominator; never turn an API failure into ALLOW or drop
it to inflate accuracy. Halt on authentication, billing, model-identity, or
systemic service problems instead of generating a misleading complete score.

Compare to the frozen WildGuard model, selected individual policy models, and
the previously frozen ensemble results where the same rows and targets match.
Identify which comparators used score calibration or learned combinations. Align
by ID and content hash; never compare different populations as if matched.
Use 2,000 paired duplicate-group bootstrap replicates for accuracy differences
between selected/calibrated and brief/default, and against named prior references.
Intervals are descriptive and unadjusted; do not claim architecture superiority.
Inspect category/adversarial slices for WildGuard and source-label/platform slices
for HateXplain after freezing, without further optimization.

## Cost, reliability, and artifacts

The previously reported experiment spend is $12.50119753456 of the authorized $20;
later skill-testing costs are separate documented usage. Set a conservative $2
ceiling for this extension including the synthetic connectivity check. Use the
published $0.042 per million input tokens and free output for estimates, record
actual OpenRouter usage.cost, and stop if billing exceeds the reserved amount or
the cap. Preserve reservations for unresolved requests. A retry is a new billed
attempt; it must be recorded and remain inside the cap.

Save the plan, exact policy variants, data manifests, raw responses, prompt-free
prediction evidence, costs, a results table, a plain-language readout, and a CPU
reproduction command. Keep credentials outside the repository and logs. The
eight-week teaching curriculum is separately recorded and remains parked.

## Primary interface sources checked 29 October 2026

- [OpenRouter Decisions API](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
- [OpenRouter Jev tutorial](https://openrouter.ai/blog/tutorials/how-to-use-jev/)
- [TypeSafe models and customization](https://docs.typesafe.ai/models)
- [TypeSafe Choice input/output contract](https://docs.typesafe.ai/primitives/choice)
- [TypeSafe state contract](https://docs.typesafe.ai/concepts/state)

These sources specify the interface and provider claims; benchmark outcomes will
come from the saved experiment evidence.
