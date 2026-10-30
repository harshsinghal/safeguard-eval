# WildGuard decision-score ensemble evidence

October 30, 2026. This exploratory follow-up combines saved native BLOCK scores
from Jev 1.14, Kev 4B, and Clef-Flash 9B. It also evaluates an open-only Kev/Clef
cohort. There were no new model calls, GPU rentals, policy edits, or language-model
weight updates. Small supervised calibrators and combiners were fitted.

Read the [plain-language findings](../../docs/decision-ensemble/README.md) and
[complete results](RESULTS.md). The primary three-model probability logistic
ensemble reached **89.32% balanced accuracy**, versus **88.69%** for the selected
Jev individual and **89.81%** for WildGuard. Its improvement over Jev was uncertain
and exchanged fewer missed violations for more false blocks. The earlier
specialist ensemble retained the stronger 91.08% point estimate.

## Procedure and scope

- **1,024 fitting prompts**, **512 validation prompts**, **1,699 test prompts**.
  The first two populations come from WildGuardTrain; the test is the labeled
  prompt-harmfulness population from WildGuardTest. IDs, text hashes and groups
  are disjoint across stages. The public test was examined in earlier studies.
- Only brief and detailed policies have complete cached fitting scores.
  Validation selected Jev detailed, Kev brief, Clef detailed. Example-bearing
  policies are excluded from new ensemble inputs, not silently imputed.
- The all-three cohort has 59 registered fitted/raw candidates; the open-only
  cohort has 48. Some individual controls are repeated between cohorts. These
  are candidate configurations, not 107 independent experiments or models.
- Balanced accuracy selects the primary configurations. Separate selections
  cover a 5% compliant-error limit and a 90% violation-catch target. We retain
  target failures and all methods, rather than picking the best test result.
- The protocol was committed at `b749b67`; development fits and all selections
  were committed at `877587a` before this extension loaded test scores.

The machine-generated training labels and human test labels differ in provenance.
Validation is reused for bounded policy and combiner selection. Candidate pools
are limited, prior tests have been inspected, and upstream training exposure is
incompletely known. Intervals are descriptive and unadjusted for multiple comparisons.

## Reproduce on CPU

Use the recorded dependencies in [requirements.txt](requirements.txt), preferably
in an isolated environment. From this archive directory:

```bash
python3 -m venv /tmp/safeguard-decision-ensemble-env
source /tmp/safeguard-decision-ensemble-env/bin/activate
python3 -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m evals.decision_ensemble.study reproduce --bundle .
```

Reproduction validates hashes, reselects policies on validation, refits all
registered candidates on fitting data, and verifies selections, parameters,
validation outputs, test scores, decisions, metrics, and paired intervals. It
does not call APIs or download models. It writes `reproduction.json`; all other
evidence stays unchanged. Python 3.9.6 and the exact package versions used are
recorded in `registration.json`.

To regenerate the readable tables from frozen results:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m evals.decision_ensemble.report --bundle .
```

`models.joblib` is our fitted-object record. The reproduction path refits rather
than loading it. Only load serialized Python objects from a source you trust.

## Evidence map

- [PLAN.md](PLAN.md), [registration.json](registration.json), and [freeze.json](freeze.json):
  protocol, original archive hashes, software versions, immutable development
  choices, and the pre-test freeze.
- [RUN-LOG.md](RUN-LOG.md): availability audit, preparation fix, validation freeze,
  test findings, and reproduction notes.
- [policies.json](policies.json) and [policy-selection.json](policy-selection.json):
  actual eligible policy text and validation selection. No raw benchmark prompts
  appear in these two policy variants.
- `inputs/`: original prompt-free native scores, decisions, IDs, labels, groups,
  and hashes, copied from the earlier immutable archives.
- [selection.json](selection.json), `validation-grid.json.gz`, and
  `validation-outputs.json.gz`: every search and frozen operating point.
- [parameters.json](parameters.json), `models.joblib`, and
  [fitting-diagnostics.json](fitting-diagnostics.json): coefficients, calibrated
  weights, forest settings, fitting counts, and log-odds clipping counts.
- `reference-selections.json` and `reference-test.json.gz`: aligned historical
  references, which never enter the ensemble feature matrix.
- [results.json](results.json), [results.csv](results.csv), and
  `test-predictions.json.gz`: metrics, category slices, score correlations,
  registered paired comparisons, raw candidate scores and selected decisions.
- [evaluation.json](evaluation.json), [reproduction.json](reproduction.json), and
  [checksums.json](checksums.json): evaluation timestamps, verification and integrity.
- `source/`: frozen implementation, supporting metric code, protocol, and tests.

Added provider cost was **$0**. The recorded cumulative project spend remains
**$13.79540555656 of $20**. No resources were provisioned or left running. This
ledger does not assign a zero cost to local CPU or researcher/assistant time.
