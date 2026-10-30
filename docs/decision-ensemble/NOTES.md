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
- [ ] Evaluate the frozen test population and paired uncertainty.
- [ ] Reproduce on CPU and document findings, limitations, and costs.

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
