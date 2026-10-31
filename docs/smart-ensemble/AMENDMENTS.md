# Preflight correction: reconstruct original policy payloads

Before any new fitting or test evaluation, the Jev development canary failed the
registered .02 score-parity check (maximum .04; zero changed native decisions).
Only 16 API requests had run, costing $0.000912366. No bulk Jev inference had run.

We identified use of the public, redacted policy pack. Its example-bearing question
was not the original private payload, even though the selected detailed policy
itself was unchanged. Reconstructing the original private pack reproduced all
16 archived request hashes. Kev/Clef example policies require the same care.

Preparation now checks the original private policy files against the prior
policy-freeze hashes and uses those exact payloads. The first canary outputs and
registration are retained as preflight evidence. The failed attempt contributes
no scores to fitting, selection or test. The original parity tolerance remains
unchanged, and the corrected canary must pass before bulk inference.

The protocol, candidate pool, metrics, fitting method and spending limit are
unchanged. Public release artifacts will preserve policy hashes and reconstruction
provenance, with restricted example text redacted as in the earlier archives.

## Amendment 2: refresh Jev's test outputs as well as development

The corrected payloads matched all 16 historical request hashes, and the API
returned the pinned Jev version and provider. Scores nevertheless differed by up
to .05, with zero changed native canary decisions. Thus redaction explained the
first payload mismatch but does not explain all observed score variation. We
cannot distinguish inference variability from an undisclosed service change.

Do not combine new fitting scores with historical Jev test outputs. Recollect
Jev development scores and, **only after the ensemble freeze**, all 1,699 and 1,924
Jev test scores using the identical private policy packs. The old canary outputs
remain a diagnostic; they are excluded from fitting and selection. Require the
same resolved model/provider and strict score schema on every call. No repeated
sampling or best-response selection is allowed on final tests.

This amendment permits the documented Jev canary drift because all stages will
use newly collected API outputs; it does not relax Kev/Clef parity checks. The
Jev budget remains $1 and the total approved cap remains $20. Conditional bootstrap
intervals do not cover this observed API variability. No test outcome motivated
this amendment.

## Amendment 3: retain an empty-content failure

The fixed WildGuard fitting population contains one empty prompt, `wgtrain-018478`.
The original Jev and native decision adapters reject empty content before inference.
Retain this row with a missing score and an explicit `ERROR` decision for Jev, Kev,
and Clef. Do not send substitute text, assign a label, or remove it from the cohort.
As already specified, fitting excludes incomplete rows only for combinations that
require their scores; unresolved evaluation cases would count as errors. None of
the development validation or canary prompts is empty. The same input rule applies
to test without consulting its labels. No test outcome motivated this correction.

The interrupted Jev pass completed its other queued requests; resume from their
request-hash caches, preserving every billed call. Kev stopped before bulk scoring.
This changes input-error handling only, not policies or selection rules.
