# Frontier API study tools

Read the [registered plan](../../docs/frontier-api/PLAN.md), [notebook](../../docs/frontier-api/NOTES.md), and [progress](../../docs/frontier-api/progress.json). **Only the fitting pilot is currently authorized**, with a $10 phase limit inside the $20 cumulative cap. The registry blocks other phases. An OpenRouter balance or a CLI invocation is not a substitute for authorization.

The pilot is now complete: [findings and archived evidence](../../published_runs/2026-10-25-frontier-pilot/README.md). Use the read-only reproduction command in that bundle to inspect it; the inference examples below describe how the completed run was launched.

## Local verification

Run from the repository root. The example data paths refer to the existing private local study files; they are not distributed in this repository.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m evals.frontier_api.estimate \
  --fit ../work/wildguard-run/data/fit-search.jsonl \
  --validation ../work/wildguard-run/data/validation-search.jsonl \
  --audit ../work/wildguard-run/data/audit-budget.jsonl \
  --test ../work/wildguard-run/test/test.jsonl \
  --out work/frontier-api/cost-estimate.json
python3 -m evals.frontier_api.run \
  --registry evals/frontier_api/registry.json \
  --data ../work/wildguard-run/data/fit-search.jsonl \
  --policy evals/wildguard/policies/p0.json \
  --arm astra-lower --stage pilot \
  --out work/frontier-api/unused-dry-run --dry-run
```

The dry run validates the full fitting file's hash/count, builds the pilot requests without displaying their text, and estimates a conservative reservation. It reads no API key and sends no network request.

## Paid phase, after user authorization

Record the actual user authorization in the registry's `budget`: `status: approved`, `authorization_note`, `approved_new_cap_usd`, and `allowed_stages`. Pilot authorization should allow only `pilot`. Keep a margin below the user cap, use the **same study ledger path for every call**, and never reset/delete a ledger to obtain more spending room. A later cap change requires explicit authorization and a documented reconciliation of the existing ledger.

```sh
python3 -m evals.frontier_api.pilot \
  --data ../work/wildguard-run/data/fit-search.jsonl \
  --out work/frontier-api/pilot
```

This rotates through all eight conditions, one request at a time, over the same first 32 fitting rows. It records every attempted call and stops if the ledger cannot reserve the next request or if routing/billing/transport fails. Inspect validity, truncation, reported reasoning tokens, and measured cost before approving the search. A pilot summary with missing costs is not a final bill; reconcile the outstanding reservation against OpenRouter generation/billing records. No automatic classification retry is made.

Use `--resume` only after a documented infrastructure reconciliation. It retains successful observations and completed invalid classifications, and preserves failed attempts. A content-filter response without usage remains ERROR and deducts its full request ceiling; it is not retried. Generic unknown billing still stops the run. Keep original manifests and any before-reconciliation files so accounting changes remain auditable.

The `run` command also supports `fit`, `validation`, `audit`, `test`, and `repeat`. Each main run checks exact source-population hashes/counts. `repeat` uses the first 256 official-test IDs and requires the same freeze as final inference. Provider aliases are not immutable weight revisions; preserve all returned deployment metadata.

## Search, freeze, and analysis

Start with the registered shared p0/p1/p2 runs. Write two new candidates per condition from fitting errors only, register their text/hash/rationale and run names, then evaluate fit/validation. Never edit a registered candidate after its evaluation. Keep private raw traces in ignored `work/`.

```sh
python3 -m evals.frontier_api.study select \
  --registry evals/frontier_api/registry.json --runs work/frontier-api/runs \
  --out work/frontier-api/selection.json
python3 -m evals.frontier_api.study freeze \
  --registry evals/frontier_api/registry.json --runs work/frontier-api/runs \
  --selection work/frontier-api/selection.json --out work/frontier-api/freeze.json
```

Selection requires five distinct complete candidates per condition; incomplete or mismatched populations are rejected. Freeze recomputes selection before accepting it. Publish the freeze before any audit/test calls. Pass it with `--freeze` to final runs. The current registry contains only the three inherited policies, so selection correctly refuses to proceed today.

For paired analysis, supply a JSON list of `{arm, policy_id, split, run}` records for every frozen policy on both `test` and `audit`. Identical policy roles share one run. `study analyze --registry … --runs … --freeze … --run-index … --out …` rejects missing final runs and reproduces failure-aware metrics and paired comparisons. Historical baseline comparisons, repetition diagnostics, cost summaries, and the public evidence bundle are reporting steps after inference; do not claim those artifacts exist yet.

Preserve the original registry, snapshots, candidates, selection, freeze, source files, run manifests, public predictions, summaries, billing reconciliation, and hashes in the eventual published run. Publish **no gated prompts, raw requests/responses, keys, or account details**. Weights remain fixed throughout.
