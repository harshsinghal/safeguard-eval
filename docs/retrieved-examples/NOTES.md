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
