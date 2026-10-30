# Next experiment: improve policy text using training errors

Status: execution authorized after review of the Shieldstral representation
results. The [concrete registered protocol](../policy-corrections/PLAN.md) and
[study record](../policy-corrections/README.md) now track this experiment.

Question: can a small, auditable set of policy revisions derived from training
mistakes reduce false blocks and missed harmful requests on held-out content,
without changing the language model's weights? Compare policy revision with
cutoff adjustment so an apparent improvement is not merely a change in strictness.

## Proposed process

1. Choose models and a starting policy before examining new evaluation outcomes.
   Preserve provider-native input formats and policy scope. Start with WildGuard
   prompt harmfulness; a later HateXplain replication needs its own policy/labels.
2. Audit earlier data usage and reserve an additional untouched, deduplicated
   holdout. Continue to report WildGuardTest for historical comparison, clearly
   acknowledging that it has already been inspected. A reserve from training
   measures that source distribution, not automatically the WildGuardTest shift.
3. Discover recurring error patterns on fitting examples. When the classifier
   itself is learned, use grouped out-of-fold predictions: an example must not
   have helped fit the classifier that supplies its error label. If policy search
   is part of that predictor, keep its data boundaries explicit as well.
4. Separate false blocks from missed violations. Diagnose policy boundaries and
   potential labeling ambiguity; model-generated explanations are hypotheses,
   not evidence of the model's internal reasoning. Do not overwrite source labels
   to improve a score. Flag ambiguous cases and document any independent review.
5. Draft a bounded number of revisions. Examples include a clearer definition,
   a necessary exception, or a paired allowed/prohibited example. Preserve the
   intended scope; record exactly which training pattern motivated each edit.
   Prefer general rules over copying particular training cases into the policy.
6. Select with a fixed validation budget, balancing both error types and checking
   predefined slices. Compare original policy, cutoff-only adjustment and revised
   policy with the same cutoff-selection procedure. A model-specific revision
   can be tested on the other model as a separately registered transfer control.
7. Freeze all edits, interfaces and thresholds, evaluate the untouched holdout
   once, and report corrected cases alongside newly introduced errors. If test
   findings motivate another revision, that is a new development cycle requiring
   a new holdout; do not advertise the reused test as untouched.
   Untouched means unused in our development; upstream checkpoint exposure to
   public datasets may remain unknown.

## Scope and interpretation

The correction artifact is versioned natural-language policy text. The current
proposal does not include LoRA, backbone fine-tuning or activation steering.
A new classification/error-detection head would be a separate training treatment,
not evidence that policy edits alone helped. Error detectors may help route cases
to review, but their confidence does not justify automatically reversing labels.

The key outcome is whether a reproducible policy-authoring process improves the
complete classifier under an explicit error budget. Improvements are not assumed;
edits can help one class while hurting another, or fail to transfer between models.
The final protocol must set models, sample sizes, iteration budget, comparison
groups, metrics and compute cap before running. No spending is booked for this
study yet, and the existing cumulative $20 cap still applies.

Relevant precedent: [ProTeGi / prompt optimization with textual gradients](https://arxiv.org/abs/2305.03495).
First study: [Shieldstral representation results](../shield-probe/README.md).
The representation experiment is complete; the correction study is now starting.
Its observed validation-to-test gap makes an additional project holdout especially
important. Do not use the first study's test mistakes to author the corrections
and then call evaluation on those same examples a held-out improvement.
