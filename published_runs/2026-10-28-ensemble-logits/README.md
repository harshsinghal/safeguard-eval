# Log-odds ensemble evidence — 28 October 2026

This local archive reproduces the log-odds follow-up without GPU inference, API keys or private prompts. The previous probability-space ensemble archive is unchanged.

| Cohort | Previous probability-feature logistic | New log-odds logistic | Change |
|---|---:|---:|---:|
| WildGuard specialists | 90.76% | 91.29% | +0.53 points |
| HateXplain specialists | 75.57% | 78.79% | +3.22 points |
| HateXplain specialists + Qwen | 78.69% | 80.82% | +2.13 points |

WildGuard's released model scored 90.35%. Calibrated Shieldstral scored 79.57% on HateXplain, exceeding the specialist-only ensemble but falling below the mixed ensemble. These exploratory results show a route to competitive performance without additional language-model weight updates. They do not establish that policy text alone is sufficient or that this route is universally easier, cheaper or better than fine-tuning.

Read the [plain-language findings](READOUT.md), [all new configurations and comparisons](RESULTS.md), [claim-to-evidence guide](CLAIMS.md), [plan](PLAN.md) and [execution notes](NOTES.md).

## Reproduce all new configurations on CPU

Use Python 3.11; the recorded runtime was Python 3.11.14. From the repository root:

```bash
python3.11 -m venv .venv-ensemble-logits
.venv-ensemble-logits/bin/pip install -r published_runs/2026-10-28-ensemble-logits/requirements.txt
LOGIT_EVIDENCE="$(pwd)/published_runs/2026-10-28-ensemble-logits"
LOGIT_PYTHON="$(pwd)/.venv-ensemble-logits/bin/python"
cd /tmp
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$LOGIT_EVIDENCE/source" "$LOGIT_PYTHON" \
  -m evals.ensemble_logits.study reproduce \
  --state "$LOGIT_EVIDENCE" --output /tmp/logit-reproduction.json
```

The command verifies checksums and freezes, reconstructs all 58 new configurations (55 fitted logistic models and three equal averages), matches validation selections, and reproduces test metrics, per-example outputs, and every registered paired interval. It also recomputes the prior 98 configurations as unchanged references. The saved `reproduction.json` records the completed check.

The verifier loads our own hash-checked joblib files. Only run it on a trusted checkout: pickle/joblib loading can execute code, and checksums alone do not authenticate an untrusted publisher.

## What is preserved

- `registration.json`, `PLAN.md`: pre-fit protocol, code/input hashes, exact reused development partitions and budget.
- `scores/`: original probability-like scores for fitting, validation and test. No source prompts are included.
- `policies/`: the unchanged policy texts and structured fields.
- `provenance/`: original development data manifest and inference-ingestion audit.
- `cohorts/*/selection.json`: every new candidate's validation metrics, coefficients, training-only scaling and thresholds, plus the expanded pool of individual controls.
- `cohorts/*/models.joblib`, `freeze.json`: frozen new estimators and hashes recorded before this extension's test evaluation.
- `cohorts/*/results.json`: all prior/new candidate metrics, primary/secondary comparisons, paired intervals, error counts and selected-model slices.
- `cohorts/*/test-predictions.jsonl.gz`: per-example outputs of all 58 new configurations.
- `reference/`: prior frozen models, selections, freezes and results, copied unchanged and hash-bound.
- `test-staging.json`: evidence that all three new cohorts were frozen before official test inputs were staged for this extension.
- `equations.json`: primary equations expressed directly in each model's reconstructed log-odds, verified against the fitted estimator.
- `descriptive-comparison.json`: explicitly post-test comparison of the mixed HateXplain ensemble with Shieldstral, the strongest individual observed on that test. This comparison never influenced selection.
- `source/`, `requirements.txt`: archived implementation, software tests, protocol and CPU runtime requirements.
- `checksums.json`: evidence inventory; `reproduction.json`: CPU verification result; `progress.json`: completion record.

## Experimental scope

The three cohorts preserve all prior selected policies, checkpoints and adapters. Each benchmark uses 4,096 fitting and 1,536 validation examples, excluded from earlier policy development and separated by duplicate groups. WildGuardTest has 1,699 labeled prompt-harmfulness rows. HateXplain has 1,924 posts; hate maps to BLOCK, offensive/normal to ALLOW. Only model scores are features. Error outputs count incorrect and cannot silently disappear.

The new representation is `log(p) - log1p(-p)` in float64. No valid score was zero or one; no clipping search was needed. These are reconstructed decision log-odds, not full native model logits. Standardization is fitted only on training data. The primary logistic ensemble and individual controls use the same five-value regularization grid and validation rule as before. Equal averaging in log-odds space is a secondary comparator. No model weights or policy words were changed.

Official tests were observed in earlier studies. Fresh freezes prevent test-based setting selection within this extension but do not remove the broader adaptive reuse. Intervals are unadjusted descriptive duplicate-group bootstrap intervals; they do not include policy-search, model-exposure or inference uncertainty. No matched fine-tuning, effort, production-latency or serving-cost comparison was performed. The mixed cohort includes a general-purpose model, so its result is not evidence that specialists alone are always sufficient.

**Added GPU/API inference: zero. Added paid compute: $0. Cumulative spend: $12.50119753456 of $20.** Local CPU and researcher/assistant time are not included in those dollar figures. No GPU instance was provisioned for this extension.
