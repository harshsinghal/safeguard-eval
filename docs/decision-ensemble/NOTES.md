# Decision-score ensemble lab notes

## October 30, 2026 — scope and availability audit

The user requested a WildGuard ensemble of System One / decision-model scores.
Native BLOCK probabilities already exist in the Jev and Kev/Clef archives.
The three models share 1,024 fitting, 512 validation, and 1,699 test rows.
Brief and detailed policies have complete coverage. Example-bearing policies
were only scored on validation and test and are excluded from the fitting pool.
No new API call, GPU rental, or language-model inference is needed.

Jev includes exact 0 and 1 probabilities, so the prior log-odds study's strict
interior-probability transform cannot be reused unchanged. The new plan fixes
clipping at 1e-6 before fitting and makes raw-score logistic regression primary.
The old studies and their no-clipping rule remain intact.

The protocol uses separate fitting and validation stages and freezes all choices
before this extension loads test scores. The public test's earlier use and the
restricted policy pool are explicit limits. The open-only cohort tests whether
a combination remains useful without an API-only component.

## Progress

Preparation initially stopped before fitting because the two source archives use
different checksum-manifest shapes (a flat map versus a `sha256` wrapper). The
loader now accepts both while verifying the same file hashes. No experiment
choice changed and no test scores were loaded by that failed preparation.

- [x] Audit native score availability and register the bounded plan.
- [x] Implement and test score alignment, fitting-only transforms, and freeze checks.
- [x] Fit on training, select on validation, and freeze all choices.
- [x] Evaluate the frozen test population and paired uncertainty.
- [x] Reproduce on CPU and document findings, limitations, and costs.

## Development freeze

Ten new experiment tests and eleven existing leaderboard tests passed. Both policy
variants align across all three models. No unresolved development outputs occurred;
fitting has 1,024 rows in 1,014 duplicate groups, validation 512 rows in 495 groups.
The two development populations are disjoint by ID, content hash and group.

The eligible-policy selection chose Jev detailed, Kev brief, and Clef detailed.
The primary three-model probability logistic selected C=10 and cutoff 0.56;
the open-only primary selected C=0.1 and cutoff 0.63. The secondary best score
method selected weighted averaging (regularization 0.1) for all three models and
a forest (depth 4, minimum leaf 80) for the open-only cohort. No test files were
present in the new bundle when these choices were frozen. All grids, parameters,
models, and source/input hashes are retained in the freeze.

## Test results and reproduction

The all-three primary scored 89.32% balanced accuracy (69 false blocks, 106 misses),
versus the chosen Jev individual's 88.69% (47 false blocks, 133 misses). The paired
difference is +0.63 points, interval −0.43 to +1.58. WildGuard's earlier frozen
configuration scored 89.81%; the previous specialist ensemble scored 91.08%.
The secondary validation-selected weighted average scored 89.08%; the highest
observed new test score, equal log-odds at 89.74%, was not promoted after test.

The open-only primary scored 87.52%, versus its chosen Kev individual's 86.91%.
The open-only validation-selected forest scored 88.10%. All test scores were
usable. Neither primary met either of its separately selected operational targets
on test. These negative and inconclusive results are retained.

Fresh CPU refits reproduced the policy selections, all 107 cohort candidate
records (including repeated individual controls), parameters, validation choices,
test scores, decisions, metrics and uncertainty intervals. Added provider cost
was zero; no resources or credentials were used. The public test's prior use and
the available-score policy restriction remain explicit in the readout.
