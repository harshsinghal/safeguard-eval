# Policy transfer: prospective experiment v1

Registered 25 October 2026, before new authoring or inference. This is an exploratory
extension of the earlier WildGuard and Qwen studies, whose test outcomes were already
observed. The aim is to test policy portability and model–policy fit, without assuming
that specialists or larger models will win.

## Questions and comparisons

1. **Transfer:** on the same recipient, does a policy selected using another model
   improve accuracy over the initial policy?
2. **Fit:** on that recipient, how does the transferred policy compare with its own
   independently selected policy? A consistent advantage for the own policy would
   support model-specific tuning; an off-diagonal win would show useful transfer.
3. **Substitution:** after every recipient sees the same pool on validation, compare
   the small specialists with Qwen3.5-27B using each recipient's frozen pool choice.
   A small-model win on this benchmark would not establish general superiority.

## Fixed design

Five frozen checkpoints: PolicyLM 1.7B, Shieldstral 3B, Qwen3.5 2B, 4B, and 27B.
Exact model and dataset revisions, data hashes, and historical baseline artifact
hashes are in `evals/policy_transfer/registry.json`.

The task is **binary prompt harmfulness**, using only the request, not the associated
assistant response. ALLOW maps to unharmful and BLOCK to harmful. No new weight
training, threshold tuning, or reasoning-mode comparison is included. Qwen uses
BF16, thinking off, greedy generation, and strict A/B parsing. Specialists retain
their previous native interfaces and the 0.5 score threshold. Errors stay in the
denominator and receive no credit. Review routing is outside this binary benchmark.

All searches start from the exact original p0. Each receives five candidate slots:
p0 plus four fresh revisions. Earlier p1/p2 and tailored policies are excluded.
The p0 fitting and validation predictions are reused from verified, pinned original
runs; no earlier selected-policy or test results enter authoring. New final p0 runs
are measured on the same rented GPU as the transferred policies.

The fixed editor is the pinned Qwen3.5-27B checkpoint, with thinking off, temperature
0, and a 4096-token output cap. A fresh, stateless, model-blinded context receives
only p0 and up to 32 mistakes from that source model's **fitting** predictions.
Selection is deterministic round-robin over gold-label/subcategory buckets, with
a seeded hash order inside each bucket. Requests are excerpted at 1200 characters
and marked when truncated. Labels may be noisy. The editor is told to generalize,
preserve policy scope, and not copy names, IDs, or distinctive case details.

The same four rewrite strategies are applied independently to each source:
benign exceptions, ordered outcome checklist, category boundaries, and a compact
version. This is a **single-round bounded search**, not repeated optimization until
a target score is reached. Only `block`, `allow`, and `precedence` may change;
purpose, label meanings, task scaffold, and model wrappers stay fixed. A maximum
1500-word policy cap applies. One format-only repair attempt is allowed; an invalid
second output consumes its slot as an explicitly recorded p0 fallback. Every
attempt and exact editor request/response is retained privately. Policy edits
receive a post-run semantic review: wording and scope changes must be distinguished.

All five candidates per model are scored on the same 1024 fitting and 512 validation
examples. The source winner maximizes validation accuracy; ties prefer fewer words
in the substantive policy fields, then lexicographic policy ID. Fit scores are
recorded, not used for selection. Validation examples/results never enter the editor.

Source winners are frozen, then transferred verbatim. The pool is p0 plus each of
the five winners, deduplicated by substantive text while preserving attribution.
Every recipient evaluates the same pool on validation. Each recipient's best pool
choice is frozen using the same rule **before** new audit or test files reach the GPU.
Duplicate model/text/split cells are reused, never counted as independent runs.

## Data and reporting

Reuse the original grouped splits and exact samples: fitting 1024, validation 512,
internal training audit 512, and all 1699 labeled WildGuardTest prompts. The official
test has 945 ALLOW and 754 BLOCK examples, excluding the same 26 null-labeled rows
as before. It is not a new unseen-category evaluation. Training labels are largely
model-produced; official test labels are human annotations. Audit and official test
have already been observed in earlier experiments and are not fresh confirmation.

Report the complete source-policy × recipient-model matrix on audit and test, with
accuracy primary, harmful F1, harmful recall, benign false-block rate, macro F1,
and errors. Report paired accuracy differences with 2000 connected-group bootstrap
replicates and seed 20261024. Intervals are descriptive and unadjusted for the many
comparisons; they do not establish equivalence or prove an optimum. Compare the
frozen pool choices for substitution, not test-selected maxima. Preserve all cells,
including regressions and generation failures.

Record GPU, precision, runtime versions, batch/concurrency settings, policy length,
request latency, run wall time, GPU rental bill, and authoring cost within the rental.
Runtime measurements include this implementation's batching and caching behavior;
they are not a production cost benchmark. Parameter count alone is not a cost claim.

## Limits on interpretation

The fixed editor is also one recipient, so editor-family affinity is a possible
confound. Only five models, four rewrites, one editor, one seed, and one benchmark
are studied. The experiment tests search procedures, not whether each model can
write its own best policy. Matching labels may change the effective policy scope;
human policy owners must review that separately from measured accuracy. A fresh
benchmark, repeated searches, and broader policy tasks are needed for stronger
generalization or non-inferiority claims.

## Execution and budget

- [x] Reconcile prior spending: $8.46119753456 of the authorized cumulative $20.
- [x] Validate original runner and 35 existing tests before changing code.
- [ ] Verify new leakage, freeze, identity, parsing, and selection tests.
- [ ] Register all inputs and source hashes; prepare GPU bundle before renting.
- [ ] Provision one GPU; RunPod is available if GPU.ai has insufficient capacity.
- [ ] Author 20 drafts with isolated fitting feedback; retain unsuccessful attempts.
- [ ] Score candidates; freeze the five source winners.
- [ ] Run cross-validation pool; freeze recipient choices.
- [ ] Upload audit/test; complete the full matrix without test-driven revisions.
- [ ] Collect and verify artifacts; terminate GPU and reconcile billing.
- [ ] Publish prompt-free evidence and a plain-language findings note.

Current GPU.ai verified capacity is an RTX PRO 6000 at $1.99/hour with no disk charge.
Use at most a five-hour server-side lifetime ($9.95), leaving about $1.59 of the
remaining authorization as reserve. Stop earlier when complete. Provider credits
do not raise the spending cap. If RunPod is needed, re-price its total compute and
storage within the same remaining budget and use a termination watchdog. Do not
launch overlapping instances or silently reduce the registered test population.
