# A balanced comparison of our saved moderation experiments

Recorded 29 October 2026, before the new configuration selection and scoring.
This is a retrospective analysis of already observed public test sets, not a new
preregistered or independent test. No API calls, GPU rentals, language-model
fine-tuning, or new combiner fitting are authorized or needed for this analysis.

## Question and scope

Which complete model–policy–adapter configurations offer a useful balance between
catching violations and allowing compliant content? Cover every model with full
WildGuardTest or HateXplain predictions, including general-purpose Qwen models,
specialist policy models, WildGuard, Jev, and all previously fitted ensemble
families. List fitting-only frontier pilots and missing benchmark cells explicitly.
Do not combine scores across different tasks into a universal model rank.

## Selection, before scoring

1. Inventory and hash the archived evidence. Pair validation and test runs by
   model revision, policy hash, adapter/format, and experiment. Exclude repeats,
   test-only ablations, and incomplete populations from candidate selection;
   disclose these exclusions. Never select a test maximum.
2. Use the same original authoring-validation population for every candidate
   within a benchmark: 512 WildGuardTrain prompts and 1,920 HateXplain validation
   posts. These have already supported policy development. They are not fresh
   holdouts. Verify exact IDs, labels, content hashes, and duplicate groups.
3. For archived calibrators and ensembles, apply the existing fitted parameters
   to saved base-model validation scores. Verify their fitting data exclude this
   common validation population and the official test by ID, content hash, and
   recorded duplicate group. Do not train new parameters. Verify reconstruction
   against archived test scores after selection is frozen.
4. A candidate can use its native decision or a numerical-score cutoff from
   0.00 through 1.00 in steps of 0.01, plus an all-allow cutoff above 1. Native
   categorical models cannot receive fictitious probabilities. Invalid responses
   remain invalid at every cutoff; do not repair them using available scores.
5. Select one candidate per individual model, and one per ensemble family and
   feature cohort, separately for three declared objectives:
   - **Balanced:** maximize balanced accuracy, then the worse class recall, then
     macro-F1; prefer native decisions, then a cutoff nearest 0.5, lower cutoff,
     and lexical candidate ID to break remaining ties.
   - **False-block limit:** maximize violation recall subject to validation
     false-positive rate at most 5%; then minimize false positives and use the
     same deterministic tie rules.
   - **Catch target:** minimize false-positive rate subject to validation
     violation recall at least 90%; then maximize recall and use the same ties.
   These are illustrative operating requirements, not recommended universal
   safety standards. Include unresolved responses in constraint error burdens:
   an unresolved compliant item consumes the false-block allowance. No feasible
   configuration means an explicit gap. Validate test attainment separately.
6. Freeze candidate hashes, selection records, metrics code, and chosen cutoffs
   before producing the new test leaderboard. Keep native/default and historical
   accuracy-selected results available as references, not as a second opportunity
   to choose a favorable test result.

The available candidate pool reflects earlier accuracy-based experiments and
unequal development budgets. Some candidate policies have no test run. "Best"
means best on the common validation set among eligible saved configurations;
it does not mean best attainable by the architecture or a controlled comparison
of equal search budgets. No new wording search takes place here.

## Test reporting

- Score exactly the same 1,699 labeled WildGuardTest prompts or 1,924 HateXplain
  posts. WildGuard measures prompt harmfulness. HateXplain BLOCK is hate speech;
  offensive and normal posts are ALLOW. No REVIEW or image task is evaluated.
- Report balanced accuracy, macro-F1, MCC, accuracy, BLOCK precision/recall,
  compliant-content allow rate, false-positive/false-negative rates and counts,
  and unresolved responses. Unresolved responses are wrong in accuracy and
  class recalls; MCC is unavailable if a row has unresolved predictions.
- Where genuine numerical scores exist, report AUROC and average precision with
  score coverage; these summarize ranking, not the selected decision boundary.
- Use 2,000 paired duplicate-group bootstrap draws for descriptive 95% intervals
  and pairwise balanced-accuracy differences. Do not claim significance from
  rank order or overlapping/nonoverlapping individual intervals. Intervals are
  unadjusted and exclude development/search and repeated-inference uncertainty.
- Show original dataset slices where supported and their sample sizes. Do not
  equate a benchmark category with a demographic fairness audit.
- Report whether the test actually meets the 5% false-block limit or 90% catch
  target. A validation constraint is not a test guarantee. Do not discard failing
  test rows or choose replacement thresholds after test inspection.

## Deliverables and checks

- A readable HTML leaderboard with benchmark/objective filters, sorting, error
  trade-off chart, provenance, coverage gaps, and downloadable data.
- Markdown results/readout plus CSV/JSON, normalized prompt-free predictions,
  selection freeze, input hashes, and a CPU-only reproduction path.
- Tests for balanced metrics, unresolved outputs, selection without test labels,
  threshold ties, constraints, aligned populations, and archived model replay.
- Preserve all earlier experiment archives and claims. Do not silently update the
  research paper, published skill, or prior headline results.

## Progress

- [x] Locate archives and identify model/benchmark coverage.
- [x] Confirm common validation examples and disjoint ensemble fitting IDs/hashes.
- [ ] Normalize eligible candidates and verify all provenance/alignment.
- [ ] Freeze validation-only choices for the three objectives.
- [ ] Score the official tests and quantify uncertainty/trade-offs.
- [ ] Build and visually verify the readable leaderboard.
- [ ] Test, reproduce, and document the findings and limitations.
