# Exactly what changed for Jev

The classifier was `typesafe/jev-1.14-20261014`, reached through OpenRouter's
Decisions API. Every request used `state.content` for the submitted text and
Choice questions with ALLOW/BLOCK answer criteria. Neither model weights nor the
test inputs changed.

## Brief to detailed

**WildGuard:** the brief version asks whether the request seeks unsafe content or
facilitates harm. The detailed version reuses `evals/wildguard/policies/p0.json`:
its purpose and precedence clauses become instructions; its BLOCK/ALLOW
descriptions become answer criteria. It spells out the harm categories, benign
educational and preventive uses, and how to handle sensitive words, quotations,
fictional framing, and jailbreak instructions. This bundles several additions; we
did not isolate each clause's contribution.

**HateXplain:** the brief version distinguishes identity-based attacks from normal
or merely offensive speech. The detailed version reuses the non-example sections
of `evals/hatexplain/policies/p0.json`: scope, definitions, target/stance guidance,
violation conditions, permitted criticism and profanity, and quotation/reporting
exceptions. It still governs hate speech alone. The original four demonstration
texts are omitted from this variant.

## Detailed to examples

Copy the detailed question without changing any clause or answer criterion.
Append four labeled fitting examples as JSON lines with `content` and
`classification` fields. The fixed selection rule takes two BLOCK and two ALLOW
cases, prefers detailed-policy errors, uses distinct duplicate groups, and prefers
unanimous annotation when available. Validation and test rows are ineligible.

All eight selected demonstrations were detailed-policy fitting errors. All four
HateXplain demonstrations had three-annotator agreement. WildGuard fitting rows
in this frozen population do not carry annotator-agreement metadata.

The evidence archive retains the selected IDs, labels, text hashes, detailed-policy
predictions, and selection method. Exact requests and the full selected policies
are preserved in the private local run. Gated WildGuard demonstration text is
withheld from the public evidence, consistent with the earlier studies; a marked
redacted copy is provided and must not be mistaken for the actual inference prompt.
Original policy hashes and serialized lengths preserve selection provenance.

## Thresholds are a separate change

After policy selection on validation, search the registered probability cutoffs.
For the selected examples policy, BLOCK when its BLOCK probability is at least
0.60 on WildGuard or 0.90 on HateXplain. The brief controls separately selected
0.55 and 0.96. These numbers are outcomes for these data and policies, not advice
to use the same cutoffs in another application.

All native choices and probability scores are retained. We did not alter scores,
train a logistic calibrator, fit an ensemble, or revise a policy after test results.
