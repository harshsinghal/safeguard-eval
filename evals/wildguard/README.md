# WildGuard policy optimization

This completed study tests whether optimizing a written policy improves frozen policy classifiers on WildGuard prompt harmfulness. It compares four custom-policy models with the released WildGuard checkpoint. The [results and reproducible evidence](../../published_runs/2026-10-24-wildguard/README.md) show within-model improvements for Shieldstral and PolicyLM, without establishing superiority over WildGuard.

The versioned [experiment plan](../../docs/wildguard/PLAN.md), [lab notebook](../../docs/wildguard/NOTES.md), [evidence ledger](../../docs/wildguard/RESULTS.md), and [progress file](../../docs/wildguard/progress.json) form the research record.

## Data and access

Accept the upstream access conditions for [WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix) and [WildGuard](https://huggingface.co/allenai/wildguard), then use your own Hugging Face token. Credentials and gated prompt text belong outside the repository. Exact revisions are in revisions.json. Source labels are never sent to the classifier.

Install data preparation dependencies `pyarrow` and `datasketch`. Download the pinned training parquet to a private directory, then:

```sh
python -m evals.wildguard.data --source /private/wildguard_train.parquet --out /private/wildguard-data
python -m unittest discover -s tests -v
```

The importer preserves every labeled source row, groups repeated and near-duplicate prompts, and generates fitting/validation/audit partitions and fixed budget samples. The test importer refuses to download WildGuardTest without a frozen manifest.

## Inference

Use an SSH tunnel to a localhost vLLM server. WildGuard uses client-side token IDs from the original slow tokenizer, the official completion template, an empty assistant response, 128 output tokens and greedy decoding. With vLLM 0.31.0, serve a local checkpoint and use a converted fast tokenizer for output decoding after verifying vocabulary identity; the old server option `tokenizer_mode=slow` is no longer available. The other generative adapters use their documented custom-policy formats. PolicyLM uses its audited, pinned native inference helper with transformers 4.57.6. The first runner release uses vLLM 0.31.0 and will record exact runtime dependencies per execution.

```sh
python -m evals.wildguard.run --adapter wildguard --model allenai/wildguard \
  --revision cbba4823f3e8020e5a74a5e29bf85072def6f2ff \
  --data /private/wildguard-data/pilot.jsonl --stage pilot \
  --out /private/runs/wildguard-pilot
```

For policy models add `--policy evals/wildguard/policies/p0.json` and select their adapter/model/revision. Score-based models use 0.5 in the primary experiment. All failures remain in the denominator. There is no REVIEW label in this benchmark.

Run directories are immutable and include a manifest, policy, predictions, summary, and `private-raw.jsonl`. The raw file contains gated input text and must not be published. Predictions omit prompts but preserve IDs, hashes, labels, scores, failures, timing and usage; inspect generated reasons before public release.

## Search and freeze

Register each candidate and its fitting/validation run paths in a JSON registry. `study select` verifies matched examples and candidate hashes, chooses a shared policy by mean validation accuracy, and chooses per-model policies by validation accuracy. Save every fitting score and rationale, including candidates that lose.

```sh
python -m evals.wildguard.study select --registry /private/registry.json --runs /private/runs --out /private/selection.json
python -m evals.wildguard.study calibrate --selection /private/selection.json \
  --registry /private/registry.json --runs /private/runs --out /private/calibration.json
python -m evals.wildguard.study freeze --selection /private/selection.json \
  --registry /private/registry.json --revisions evals/wildguard/revisions.json \
  --audit /private/wildguard-data/audit-budget.jsonl \
  --data-manifest /private/wildguard-data/manifest.json \
  --calibration /private/calibration.json --final-fit /private/wildguard-data/fit-expanded.jsonl \
  --out /private/freeze.json
python -m evals.wildguard.prepare_test --freeze /private/freeze.json --out /private/test
```

Set `HF_TOKEN` securely for the final command. Audit/test runs require `--freeze`; policy, model, source, settings and dataset provenance must match. Threshold calibration is a separate validation-only control, never part of the primary policy-only comparison.

The evidence package distinguishes full datasets from budget samples, source-label ambiguity from model errors, and within-model tuning gains from cross-model comparisons. No article should claim a general advantage for policy tuning from a single public benchmark.

Create the expanded fitting sample with `sample(fit_rows, 8192)` and `write_jsonl` from `evals.wildguard.data`; use the already assigned fitting partition. The registered run uses the same deterministic seed and stratification as the smaller samples. Save its SHA256 in the freeze.

## Analysis and publication

After frozen inference, `overlap` audits lexical train/test overlap without filtering the primary score. `analyze` verifies all frozen test configurations are present and computes paired group-bootstrap intervals, deduplicated and overlap sensitivities, and the validation-selected threshold controls. `export` publishes gzip-compressed predictions through an explicit field allowlist, omitting source prompts, generated reasons, and private request/response traces.

```sh
python -m evals.wildguard.overlap --train /private/wildguard-data/train.jsonl \
  --test /private/test/test.jsonl --freeze /private/freeze.json --out /private/overlap.json
python -m evals.wildguard.analyze --runs /private/runs --freeze /private/freeze.json \
  --overlap /private/overlap.json --out /private/analysis.json
python -m evals.wildguard.export --runs /private/runs --out /public/evidence
```

Policy search is agent-authored and directed by fitting-error inspection; it is not an exhaustive or globally optimal search. Aggregate validation scores were visible during the search, but validation prompt/error inspection was prohibited. The final official test was kept unopened until selection and threshold freeze. Independent repetition of the search is future work.

The [reproduction instructions](../../published_runs/2026-10-24-wildguard/REPRODUCING.md) explain how to recompute all published scores and paired intervals without a GPU or API key, using either the current tools or the archived source snapshot.
