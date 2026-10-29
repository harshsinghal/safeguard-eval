# Balanced moderation leaderboard: evidence and reproduction

**[Open the interactive leaderboard](index.html)** ·
**[Read the plain-language findings](READOUT.md)** ·
**[Full tables](RESULTS.md)** · **[CSV](leaderboard.csv)**

On GitHub, download `index.html` and open the downloaded file in your browser.
It embeds its data and works offline. Links to companion files work when the
bundle/repository is also downloaded. The HTML is a local artifact, not a newly
published public website.

This retrospective comparison covers **197 eligible saved configurations** and
**18 entries per benchmark**. WildGuard has 11 individual models and seven
ensemble methods. HateXplain has four individual models and seven methods for
each of two ensemble component sets. Full coverage includes the four frontier
API models as explicitly unranked fitting-only pilots.

The highest observed balanced scores were **91.08%** for the WildGuard specialist
equal-log-odds average and **79.35%** for the HateXplain specialist-plus-Qwen
log-odds logistic ensemble. Nearby scores often have unresolved uncertainty.
Use the paired comparisons and both error rates before drawing a conclusion.

## Selection and scope

All entries use the same validation population within a benchmark: 512
WildGuardTrain prompts or 1,920 HateXplain posts. Selection maximizes balanced
accuracy or meets one of two separately declared operating requirements. The
entire choice of candidate and threshold is frozen in `selection.json` and
`freeze.json` before this analysis scores the official tests. Test results were
already known from earlier work, so this is exploratory rather than independent
confirmation.

Test populations are the same 1,699 labeled WildGuardTest prompts and 1,924
HateXplain posts used previously. HateXplain maps hate speech to BLOCK and normal
or offensive posts to ALLOW. These are binary text tasks, with no REVIEW route.

The 5% false-block and 90% catch requirements apply on validation. The report
separately shows whether they hold on test. None of the WildGuard selections met
either test target. On HateXplain, 16/18 met the false-block limit and 2/18 met
the catch target. The thresholds were not replaced after seeing those outcomes.

Existing calibrators and ensembles were replayed on the common validation set,
using fitting data verified to be disjoint by ID, text hash, and duplicate group.
Their parameters were not retrained. All **140 calibration and ensemble test replays**
matched archived scores and decisions. Earlier policy searches, datasets used
for original model training, and development budgets differ across models.

## Bundle contents

- `registry.json`: every eligible candidate, model/policy/adapter identity,
  source paths, and fitted-parameter provenance.
- `coverage.json`: complete model/benchmark coverage and excluded runs. Test-only
  format ablations and missing test runs cannot enter validation selection.
- `validation/*.json.gz`: common metadata and normalized candidate outputs.
- `validation-grid.json.gz`: all evaluated development decision rules.
- `selection.json`, `freeze.json`: immutable development-only decisions and
  original input/source hashes.
- `test/*.json.gz`: normalized complete official-test outputs, including native
  decisions and genuine numerical scores where available.
- `results.json`: metrics, intervals, paired differences, error counts, native
  reference scores, source-category slices, and test target attainment.
- `replay-verification.json`: exact verification of archived fitted-model replay.
- `source/`: analysis and reproduction source, with required existing helpers.
- `reproduction.json`, `progress.json`, `checksums.json`: verification and status.

The bundle contains IDs, hashes, labels, scores, and category metadata. It contains
no original content, generated reasoning, request headers, API credentials, or
newly redistributed gated training text. Original experiment archives remain
unchanged. Jev's HateXplain export omitted group IDs; canonical groups come from
the original dataset archive after exact ID/label/content-hash alignment.

## Reproduce without APIs or GPUs

Use Python 3.11 and the recorded versions in `requirements.txt`. From this bundle:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=source .venv/bin/python -m evals.leaderboard.build reproduce --bundle .
```

This recomputes the validation choices, metrics, slices, 2,000 group-bootstrap
intervals, and 306 paired balanced-accuracy comparisons, then checks exact
agreement with `results.json`. It does not read an API key, call an inference
provider, or load a language model. Install dependencies only if needed; the
project's existing analysis environment can run the command directly.

To rebuild from the original repository archives into a **new** directory:

```sh
python -m evals.leaderboard.build prepare --repo . --bundle /tmp/new-leaderboard
python -m evals.leaderboard.build evaluate --repo . --bundle /tmp/new-leaderboard
python -m evals.leaderboard.render --bundle /tmp/new-leaderboard
```

The rebuilding path only loads checksum-verified fitted artifacts from this
project. It does not fit new estimators. Never load an untrusted pickle/joblib
file as a substitute for the recorded artifacts.

## Metric and interpretation notes

Balanced accuracy averages class-specific recall. Unresolved outputs remain
wrong in accuracy and class recalls. False-positive/false-negative counts record
actual wrong decisions; unresolved counts are shown separately. For operating
constraints, unresolved compliant outputs consume the false-block budget. MCC is
unavailable when unresolved predictions exist, rather than calculated on a
silently reduced population.

AUROC and average precision use genuine numeric scores on successful outputs,
with score coverage reported. They describe score ranking, not the deployed
cutoff. A categorical answer is not converted into a probability.

Intervals are unadjusted, conditional on saved outputs, and exclude search and
inference uncertainty. The public tests were reused; the candidate pool is
limited by earlier experiments and original model training exposure is not fully
known. WildGuardTrain labels are GPT-4-derived, whereas official-test labels are
human-annotated; WildGuard itself trained on WildGuardTrain. No universal model
winner or production error guarantee follows from this leaderboard.

**Incremental API/GPU cost: $0. No new inference or fitting.** Local CPU time and
researcher/assistant effort are not included in that provider-cost statement.
