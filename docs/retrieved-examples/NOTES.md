# Retrieved-example study notes

## Registration and scope

The user authorized an accuracy comparison using PolicyLM, Shieldstral, Jev and
one open decision model, with policy-only, four fixed, four nearest, two nearest
per class, and nearest-neighbor-only controls. No calibration or latency study.

The prior native-decision validation table selects Kev over Clef: Kev brief
464/512, detailed 457/512, examples 428/512; Clef brief 456/512, detailed 442/512,
examples 454/512. This selection does not use current test outcomes.

The existing cumulative spend is $19.36001787256. A read-only GPU.ai check found
zero running instances. Local preparation proceeds without paid inference.

## Local preparation completed

The library contains 1,814 distinct fitting groups: 756 ALLOW and 1,058 BLOCK.
The recorded length/content filter excluded 2,138 fitting rows and collapsed 144
additional eligible duplicates. No conflicting-label group occurred in this
fitting population. Validation and the example library have disjoint groups.

The frozen E5 encoder ran locally on CPU in float32. Complete long-query windows
were pooled as registered; validation required 1,553 windows for 1,536 prompts,
with at most six windows for one prompt. No query was clipped. Fitting smoke
retrieval prepared 128 requests per model; validation prepared 6,144 per model.
The final test retrieval and all classification-model calls have not run.

Twenty-two focused tests passed across the new retrieval code and reused
decision/API primitives. A full prepared-input audit checked neighbor membership,
four distinct examples per retrieval condition, body hashes, and input/label
separation. A pre-inference registration amendment adds two imported policy/model
configuration modules to the code-hash list; it changes no input or experiment
choice. The original registration is retained privately for provenance.

The initial implementation and protocol were published at `1ac1c7a`. The user was
asked for up to $3 additional allowance, raising the prior cumulative cap to $23.
Until an explicit reply arrives, paid work remains pending. Local preparation
has incurred no API or GPU charges.

## Fresh budget authorized

The user authorized a **fresh $20 budget for this experiment**. This replaces the
pending $3 request. Prior accounted spending of $19.36001787256 is reported
separately and does not consume this new allowance. The first bounded rental
reserves at most $2.60 (four hours at $0.65/hour); Jev reserves up to $1.00.
No changes to the registered comparisons, policies, examples or fixed decisions.

## Native PolicyLM formatting amendment

The fitting-only PolicyLM smoke run rejected the demonstration suffix before
producing predictions: its native Category interface requires every field to be
one line. Before native validation or any final testing, replace the presentation
newlines with spaces for PolicyLM alone. JSON-escaped newlines inside the actual
example strings are preserved, as are example content, labels, order, base rules
and the 0.5 cutoff. This is an input compatibility fix, not a search over example
wording. The original source, registration, job hashes and rejection log are
retained. The previous private job files are also retained without publication.

All Jev, Kev and Shieldstral request hashes remain unchanged. Jev had completed
validation before this amendment; its metrics had not been inspected. Its
predictions are retained without rerunning. Twenty-two focused tests pass after
adding a regression check for PolicyLM's single-line requirement.

## Shieldstral batch consistency amendment

The fitting-only batch-8 check changed Shieldstral scores by at most 0.015083,
exceeding the registered 0.005 tolerance, while changing none of the 16 decisions.
Before native validation or final testing, switch Shieldstral to batch size 1
throughout. This prioritizes consistent single-request scoring; it is not an
accuracy-driven runtime search. Preserve the rejected parity record and log.
PolicyLM already uses batch size 1; Kev remains subject to its own parity check.
No policy, examples, output cutoffs or model weights change.

Kev's first smoke attempt also found a missing runtime dependency (`pydantic`).
Install and pin version 2.12.5 before any Kev predictions; retain the failed
startup log and complete environment lock. This does not change model inputs.

## Boundaries for interpreting the study

This study changes the examples supplied to an existing policy. It does not
rewrite the base clauses, train an embedding model, fit a classifier, or select
a new output threshold. The nearest-neighbor control still depends on labeled
training data; the comparison is not evidence that labels are unnecessary.

Only one fixed set of four examples and one embedding model are tested. Adding
examples also adds input length, and similarity can reflect shared topics rather
than the same policy boundary. The balanced condition helps test label balance
but does not isolate every difference in example content and order. PolicyLM's
category-field conditioning differs from the decision models' instruction
conditioning, so differences between model families have several possible causes.

The official test was used in earlier project studies and might also have been
seen during checkpoint development. The fitting library uses WildGuardTrain's
largely model-derived labels; the official test uses a different annotation
process. The within-model comparisons are useful exploratory evidence, not a
fresh independent estimate of production quality. No enterprise-data, multilingual,
image-moderation, HateXplain, latency or end-to-end cost claim is added by this run.

## Validation freeze before final test

All 24,576 validation classifications completed and their request hashes matched
the frozen inputs. PolicyLM and Shieldstral nominated policy-only; Kev and Jev
nominated two-nearest-per-class examples. These are validation selections, not
final-test findings. All four conditions will still be evaluated for every model.

The freeze SHA-256 is
`eaa10e9c0a31155a43905bf29a9e1767a8e170dfadbf8604c4618017b0319373`.
The public registration and validation freeze are committed before creating test
retrieval jobs or starting test inference. No base policy, model weights,
retrieval choices, example counts or output cutoffs are revised after this freeze.

## Frozen test inputs and runtime diagnostics

The freeze was published in commit `78e2768` before test retrieval and inference.
All 1,699 targets passed the input audit. The E5 retriever used one window for
1,695 targets and two for four targets, with no clipped query. Bank and test
duplicate groups are disjoint; only training labels enter demonstration text.

On validation, PolicyLM used identical native message-window counts in every
condition (1,516 single-window targets; 20 multi-window targets). The same two
targets triggered its native cleaning in every condition. Shieldstral's top
vocabulary token was yes or no for all validation classifications. These are
interface diagnostics, not evidence about a causal mechanism for accuracy.

Jev completed all 13,068 API classifications across smoke, validation and test.
The reported API total is $0.344933148, with no unresolved cost reservations.
GPU usage was reconciled after all test outputs were collected: $0.53 for 2,929
billed seconds, making the complete experiment $0.874933148. The provider confirmed
termination, listed zero active instances, and temporary SSH keys were removed.

## Completed comparison

All 52,272 model result records (smoke, validation and test) are retained, plus
separate fitting-only parity diagnostics. All 27,184 final model decisions and
1,699 neighbor-control predictions are present. Input and request hashes match;
no example, cutoff or selection changed after the freeze. Independent scikit-learn
checks matched accuracy, balanced accuracy, macro-F1 and confusion counts for all
17 test conditions.

Four nearest examples changed accuracy by −2.35 points for PolicyLM, −1.12 for
Shieldstral, +0.65 for Kev and +0.18 for Jev. The Kev/Jev gains versus policy-only
have intervals including zero. Kev nearest versus fixed examples gained 1.06
points (unadjusted interval +0.18 to +2.00), but that does not establish a gain
over its policy-only control. The frozen balanced selections improved Kev by
10 and Jev by eight test decisions, with uncertainty including no gain. The
neighbor-only control scored 70.04%.

PolicyLM fixed examples were slightly better on test but were not the validation
nomination. Kev nearest examples exceeded its balanced nomination by only one
test decision. Neither result replaces the frozen selection. Results support
model-specific evaluation of example conditioning, not a general retrieval gain
or an architectural explanation. Exact policies, inputs, outputs, amendments and
bootstrap comparisons remain traceable through hashes and the public archive.
