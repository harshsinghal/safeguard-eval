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

- [x] Audit native score availability and register the bounded plan.
- [ ] Implement and test score alignment, fitting-only transforms, and freeze checks.
- [ ] Fit on training, select on validation, and freeze all choices.
- [ ] Evaluate the frozen test population and paired uncertainty.
- [ ] Reproduce on CPU and document findings, limitations, and costs.
