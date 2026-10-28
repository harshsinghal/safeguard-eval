# Turn policy intent into a tested policy

This is practitioner guidance drawn from the experiments, not a tested enterprise
product or a universal policy format. Source IDs resolve through
[sources.json](sources.json).

## Start with the decision the policy owner wants

Clarify the content being judged, the prohibited behavior, permitted uses, and
which exceptions take precedence. A higher benchmark score is not authorization
to change those boundaries. In the transfer study a selected draft omitted an
explicit category; in HateXplain a draft was rejected for changing definitions.
Those are concrete reasons for policy review alongside model evaluation.
Sources: `transfer-edits`, `hatexplain-scope`.

A useful authoring source can include:

| Component | Question it answers |
|---|---|
| Version and scope | Which rule set is this, and what content does it cover? |
| Definitions | What do the key categories mean? |
| Violation rules | What must be blocked? |
| Permitted cases | What should remain allowed despite superficially similar words? |
| Exceptions and precedence | Which rule wins when two seem to apply? |
| Labelled examples | Where are the difficult boundaries? |
| Decision contract | Which labels and scores can the model return, and how are they used? |

For example, an **untested teaching draft** about sharing private phone numbers
might prohibit posting another person's private number, allow a company's public
support number, and distinguish reporting a privacy problem from exposing a
number. The owner would still need to decide how consent, fictional examples, and
missing context should be handled. This project has not validated that PII task;
the example does not establish detection performance or require a separate scanner.

## Adapt the source to the model

Use [models.md](models.md) and the source `interface-audit`. Keep the source policy
readable for its owner; let an adapter deliver the supported components in the
checkpoint's native form. Check that all clauses and exceptions survive rendering,
that content is separate from instructions, and that the input fits the model's
limits. Record the final rendered input or its hash for reproducibility.

Preserving every clause is a representation check. Applying those clauses as
intended is a behavior check. Passing the first does not imply passing the second.
If a component is unsupported, report that fact and decide how to handle it; do
not silently omit it. Do not claim the historical runners are production SDKs.

## Change one kind of thing at a time when testing a cause

| Change | What to hold fixed if the question is its effect |
|---|---|
| Rule wording or category definition | Model, native adapter, decision rule, examples |
| Examples | Intended rules, model, adapter, cutoff; document removed information |
| Headings, order, or prose presentation | Clause text and information content |
| Transfer to another model | Policy body; retain each recipient's fixed native adapter |
| Decision cutoff or calibration | Policy, model weights, saved scores |
| Ensemble method | Constituent policies/models, aligned examples, selection budget |

When several things change together, report the combined treatment. The first
WildGuard study did not isolate every sentence. HateXplain separately tested
presentation and omissions. These are different experimental questions.

## Keep a small but credible evaluation loop

1. Define labels with the policy owner. Include legitimate near misses and
   exceptions, not just obvious violations. Keep related or duplicate examples in
   the same partition so they cannot leak across fitting and evaluation.
2. Use fitting examples and their errors to propose edits. Review whether each
   edit preserves the intended policy. Save rejected drafts and the reason.
3. Choose among candidates and decision settings using validation. State the
   objective before selection: accuracy, macro-F1, recall at an acceptable false
   block rate, or another outcome suited to the workflow.
4. Freeze the policy, model revision, adapter, output parsing, and decision rule.
   Evaluate on the reserved test examples and keep failures in the denominator.
5. Review false blocks, missed violations, important content slices, and paired
   examples that changed. A single blended metric can conceal a trade-off.

Use confidence intervals and repeat runs when close results or runtime variation
matter. If earlier test outcomes have already shaped the study, call the extension
exploratory and reserve fresh confirmation data. Do not repeatedly revise against
the same test and then describe it as unseen evidence.

The repo's study-specific designs are sources `wildguard-methods`, `hatexplain-plan`,
and `logits-plan`; copying a split size does not guarantee a good new benchmark.

## If combining scores

Compare against properly selected individual controls. Align example IDs and score
orientation. Normalize the intended label scores, document what they mean, and
fit transformations and combiners on fitting data only. Select hyperparameters
and thresholds on validation; never train on test labels. Saved probabilities
are not necessarily calibrated probabilities of real-world harm.

The log-odds extension fitted a small supervised classifier over frozen model
outputs. It did not further fine-tune the language models. Its specialist-only
HateXplain ensemble did not beat the selected individual specialist. More models
also mean more serving work unless a different routing design is separately tested.
Sources: `ensemble-results`, `logits-results`, `logits-claims`.

## Share ownership of the resulting behavior

Policy owners define intent, permitted cases, and acceptable errors. Engineers
verify adapters, scoring, failure handling, runtime behavior, and deployment.
Together they approve the tested combination and its trade-offs. Version a policy
change with its evaluation evidence and retain a way to restore a previous version.
This is a practical implication of the studies, not a measured organizational outcome.

For an enterprise assistant, policy checks should complement source permissions
and retrieval controls. These experiments do not show that a prompt classifier
can reliably infer hidden employee intent or repair incorrect access controls.
See the proposed `enterprise-track` rather than claiming those use cases were tested.
