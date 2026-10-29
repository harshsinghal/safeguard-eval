# Learn a method, then test your own policy

Use this guide when a learner wants to apply a finding or design an experiment.
The research shows questions worth asking. It does not establish what their
policy, model, language, or community will do. Keep the explanation proportional
to the task: one worked example often teaches more than a catalog of studies.

## Be exact about what kind of answer you are giving

Weave the distinction into ordinary prose; do not require these labels on every
paragraph:

- **Recorded result:** “In the project's WildGuard transfer study…” Attach the
  named models, selected policy, comparison, and source to the claim.
- **Interpretation:** “This suggests testing a policy again when the model changes.”
  The implication is narrower than a claim that transfer always fails.
- **Teaching example:** “For this fictional community, suppose…” The expected
  labels come from the stated rule and need the policy owner's agreement.
- **Proposed experiment:** “You could compare these two drafts…” Predictions are
  hypotheses until measured. A proposed test is not permission to spend money.
- **Open policy choice:** “The rule does not yet say whether…” Identify the missing
  boundary and develop the rest of the draft while the owner decides.

For a historical question, retrieve before explaining. For a new policy question,
reason from the user's rule rather than treating benchmark labels as universal
moderation judgments. A number from another model, a provider recommendation,
and an illustrative example cannot replace missing evidence for the requested case.
Keep a numerical claim attached to its named model and the source that contains
it. Adding an unnecessary leaderboard to a targeted answer creates more claims
to verify without helping the learner. For transfer, repeat the concrete direction
from the lookup; A's validation selected a policy for A before it was evaluated
on B. Do not describe that as A selecting a policy for B.

## Check examples before teaching from them

For each suggested decision, check four things: the content actually supplied,
the rule it could trigger, the exception that may protect it, and the condition
that permits review. Present the decisive reason, not an internal reasoning trace.

For example, under a rule against direct personal insults that permits reporting
abuse, “Something upsetting happened at work” contains no direct insult. A lack
of detail does not itself trigger review. A quoted insult plus an insult added by
the writer is a different case: the quotation exception may protect only the
reported words. These are untested teaching examples under this rule, not rules
for every community. Other independently applicable policies are a separate scope.

If it is genuinely unclear whether quotation or endorsement is prohibited, the
policy needs a decision. Do not silently turn that uncertainty into a model class.
“Unresolved in the draft” describes unfinished authoring; REVIEW describes an
operational action that needs an agreed trigger and implementation.

Do not overlook evidence that resolves the case. Under the report-permitting rule
above, “A colleague called me 'stupid'” is an attributed report, and “He called me
that word again” remains a report without a displayed attack by the writer. Both
are allowed by that rule. A real review candidate might contain potentially
insulting language without enough context to tell who is speaking or targeted;
the owner must have agreed that this situation triggers review. Merely imagining
that an allowed report could conceal an attack is not supplied evidence.

The rule itself also needs a scope check. If the user bans selling products, do
not silently add buying, every recommendation, services, or all promotion. Related
commercial behaviors can be proposed as separate choices. Show a meaningful change
in scope as a decision for the owner rather than a polishing edit.
The same applies to narrowing: a rule against personal insults does not become
limited to insults aimed at registered members just because the venue is a forum.
Keep the stated target scope. Do not introduce an ambiguity by changing it, then
ask the user to repair the ambiguity the draft introduced.

When a user corrects an example, update the affected clause and examples. Preserve
other decisions. In particular, “do not review harmless vague reports” does not
mean “remove every review route.” An unresolved choice can remain explicitly open
in a useful handoff.

## Choose a small experiment that answers their question

### Does an exception improve the decisions we care about?

The project changed policy wording on WildGuard, and tested omissions separately
on HateXplain. Outcomes differed by model and decision setting; there is no
universal edit that improves every policy. See `wildguard-results`,
`wildguard-claims`, and `hatexplain-readout` in [sources.json](sources.json).

For a user's own task, compare a starting draft with one that states a previously
implicit exception. Keep the model, native adapter, decision cutoff, and evaluation
cases fixed. Predict which mistakes the edit should reduce, and which it might
increase. For example: fewer false removals of people reporting abuse, without
more missed direct attacks. Check that the edit expresses the intended boundary;
do not simply weaken the rule to improve a score.

This tests that specific change. It does not establish that the longer draft is
better in general or identify which sentence mattered if several things changed.

### Does a policy selected for one model help another?

The transfer study tested the same selected texts across recipients with their
native adapters. Read the exact direction with the bundled lookup described in
[studies.md](studies.md); “selected for” names the feedback and selection model,
not necessarily the model that wrote the words.

For a new experiment, develop a candidate using model A's fitting examples and
choose it on validation. Freeze the candidate. On model B, compare that candidate
with B's starting policy, keeping B's adapter and decision settings fixed. Also
compare with B's own validation-selected policy if the question is whether
transfer substitutes for tuning on B. Include both directions only if that is
the question; do not call an A-to-B result a B-to-A result.

Use the same reserved test cases for the frozen comparisons. Report the policies
actually selected, including an unchanged starting policy. This establishes a
result for those combinations, not a ranking of the models' best possible results.

### Is a better score really due to better policy text?

The project's calibrated controls showed why this matters: changing a decision
cutoff could shift many outcomes without changing the policy. See
`wildguard-claims` and `ensemble-results`.

Hold the cutoff fixed when isolating a text edit. If deployment settings will be
tuned, also compare candidates after giving each the same validation procedure
for choosing a cutoff. Keep those two comparisons distinct. A score combiner is
another experiment with its own supervised fitting; it is not needed for a first
policy-writing lesson.

## Start small without pretending a demonstration is validation

A learner can begin with a handful of fictional or sanitized examples, label them
before trying a model, and discuss disagreements with a policy colleague. This
checks understanding and catches obvious problems. Do not assign a universal
minimum sample size or claim that five, ten, or fifteen examples establish quality.

For a measured comparison, use representative cases, legitimate near misses,
exceptions, and relevant content slices. Explain three roles for the data:

- Fitting examples reveal errors and help revise the draft.
- Validation examples choose among drafts and decision settings.
- Reserved test examples measure the frozen choice.

Keep duplicates and related cases together. Do not show expected labels to the
classifier. Examples used in policy writing have become development material,
including examples suggested in this conversation. If test results influence
another revision, disclose that reuse and seek fresh confirmation cases. Benchmark
labels are useful only when their definitions match the user's intended task.

Decide beforehand which errors matter and how to compare them. Inspect false
blocks and missed violations separately, alongside overall scores. For an agreed
review route, also examine how much content is deferred, which cases are deferred,
and errors among automatically decided cases. Do not count abstentions as correct
or import a binary benchmark score as evidence for a three-way workflow.

## Leave the learner with something they can use

Offer a short, editable experiment brief when useful:

> **Decision:** What content and rule are we evaluating? What remains undecided?
> **Hypothesis:** Which mistake should this edit or model change reduce?
> **Comparison:** What are the two configurations, and what stays fixed?
> **Examples:** How will labels be agreed, with development and reserved cases separated?
> **Success and trade-offs:** Which mistakes matter, and what would make us reject the change?
> **Record:** Save policy versions, model revisions, native inputs, settings, predictions, failures, and usage.

The policy owner owns intent and acceptable trade-offs. Engineering verifies
rendering, scoring, runtime behavior, and reproducibility. This division is guidance
derived from the work, not an organizational outcome measured by the benchmarks.
Offer one relevant continuation, such as “Let's build the expected-decision table”
or “Let's turn this into a comparison plan.” Respect a request to stop or be brief.

Use [authoring.md](authoring.md) for detailed evaluation design and
[running-models.md](running-models.md) only when execution becomes relevant. Teaching
and planning require no classifier download, rented GPU, or new paid inference.
