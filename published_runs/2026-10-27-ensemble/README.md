# Frozen-policy ensemble study — 27 October 2026

This package contains the scores, learned combiners, frozen choices, test results and source needed to reproduce the ensemble study without GPUs or API keys. It is a local evidence archive; no new public release is implied by its directory name.

Read the [plain-language findings](../../docs/ensemble/READOUT.md), [complete results](../../docs/ensemble/RESULTS.md), [protocol](PLAN.md) and [lab notebook](../../docs/ensemble/NOTES.md).

## Main results

| Cohort | Validation-selected individual | Primary logistic ensemble | Validation-selected ensemble |
|---|---:|---:|---:|
| WildGuard specialists | 90.88% | 90.76% | 90.88% — weighted average |
| HateXplain specialists | 79.57% | 75.57% | 79.31% — random forest |
| HateXplain specialists + Qwen | 79.16% | 78.69% | 79.73% — random forest |

The registered equal raw average reached 91.41% on WildGuardTest, versus 90.35% for the WildGuard model and 90.88% for calibrated Shieldstral. It was not the validation-selected ensemble. The mixed HateXplain forest exceeded the strongest observed individual, Shieldstral, by only three correct answers; its macro-F1 and hate recall were lower. All methods and negative results are retained.

The tests contain 1,699 labeled WildGuard prompt-harmfulness examples and 1,924 HateXplain posts. HateXplain maps hate speech to BLOCK and offensive/normal to ALLOW. All model weights and policy texts stayed fixed. Each cohort fit its combiner on 4,096 rows and selected settings on 1,536 separate validation rows, with duplicate groups kept apart. These development rows were excluded from earlier policy development. Official tests were reused, making the results exploratory.

## Reproduce on CPU

Use Python 3.11. The recorded environment was Python 3.11.14. From the repository root:

```bash
python3.11 -m venv .venv-ensemble
.venv-ensemble/bin/pip install -r published_runs/2026-10-27-ensemble/requirements.txt
ENSEMBLE_BUNDLE="$(pwd)/published_runs/2026-10-27-ensemble"
ENSEMBLE_PYTHON="$(pwd)/.venv-ensemble/bin/python"
cd /tmp
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ENSEMBLE_BUNDLE/source" "$ENSEMBLE_PYTHON" \
  -m evals.ensemble.reproduce \
  --bundle "$ENSEMBLE_BUNDLE" --output /tmp/ensemble-reproduction.json
```

The command verifies file checksums, checks split separation, refits every registered candidate, confirms the validation selections and thresholds, and recomputes every test metric and all registered paired intervals. `--skip-refit` verifies frozen fits and metrics without retraining the small CPU models. Neither mode calls a model API or starts a GPU.

The verifier loads the package's own hash-checked `models.joblib` objects. Joblib/pickle files can execute code when loaded: run this only on a trusted checkout, not a replacement archive from an unknown source. Checksums detect changed files; they do not authenticate an untrusted publisher.

## Evidence map

- `cohorts/*/freeze.json`: exact policies, model revisions, development/test hashes and fitting-code hashes recorded before test evaluation.
- `cohorts/*/selection.json`: every candidate's development settings and validation metrics, including averaging weights and logistic coefficients.
- `cohorts/*/models.joblib`: frozen calibrators and combiners; no language-model weights.
- `cohorts/*/results.json`: all candidates' test metrics, selected comparisons, group-bootstrap intervals, error overlaps and selected-model slices.
- `cohorts/*/test-predictions.jsonl.gz`: per-example decisions for all candidates, without post/prompt text.
- `scores/`: aligned fit, validation and test scores for all base models. The WildGuard model is an external comparator, never an ensemble input.
- `policies/`: exact frozen policy texts and structured fields.
- `new-runs/`: fresh HateXplain run manifests, native policy renderings and completion hashes. Request text and raw traces remain private.
- `data-manifest.json`: sampling, excluded earlier runs, duplicate grouping, label counts and source hashes. Original private source paths are provenance, not prerequisites for CPU reproduction.
- `inference-registration.json`, `ingestion.json`: pinned inference setup, score-ingestion hashes and 32-score consistency checks per model.
- `descriptive-comparison.json`: explicitly post-test comparison of the mixed HateXplain forest with Shieldstral; it never affected selection.
- `source/`: the CPU fitting/evaluation/reporting implementation and software tests at archive time.
- `inference-source/`, `runtime/`: registered native-adapter source and exact GPU runtime packages. Rebuilding fresh inference additionally requires the prior study's dependencies, pinned checkpoints and authorized benchmark text.
- `billing.json`: reconciled GPU.ai usage, confirmed termination and cumulative cost.
- `checksums.json`: SHA-256 inventory. `reproduction.json` records the completed CPU verification.

Scores contain source labels and other audit metadata, but the combiner receives only the model scores. Metadata and labels never enter its feature matrix. Predictions with missing/failed required inputs remain errors and count incorrect; no examples are silently discarded. This run had no fresh inference errors.

The selected methods use two or three base-model evaluations per example. Archived concurrent request timings are not a production latency or serving-cost benchmark. This run required only development inference: 16,896 new development scores plus 96 consistency scores. GPU.ai billed 691 seconds for **$0.38**; the instance is terminated. Cumulative experiment spending is **$12.50 of $20**. RunPod was available but not needed.

## Limits on interpretation

The primary method was logistic regression, not the method that scored highest after seeing the test. Confidence intervals are unadjusted descriptive group-bootstrap intervals and omit policy-search/inference uncertainty. The reused tests do not constitute an independent confirmatory trial. This experiment does not establish production readiness, multilingual performance, reliable REVIEW routing, or a universal best ensemble. It evaluates fixed policy/model combinations and a bounded combiner search.
