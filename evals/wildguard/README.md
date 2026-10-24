# WildGuard policy optimization

This study tests whether optimizing a written policy improves frozen policy classifiers on WildGuard prompt harmfulness. It compares four custom-policy models with the released WildGuard checkpoint. Results are pending; improvement over WildGuard is a hypothesis.

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

Use an SSH tunnel to a localhost vLLM server. The WildGuard model requires the slow tokenizer and uses the official completion template, empty assistant response, 128 output tokens and greedy decoding. The other generative adapters use their documented custom-policy formats. PolicyLM uses its audited, pinned native inference helper with transformers 4.57.6. The first runner release uses vLLM 0.31.0 and will record exact runtime dependencies per execution.

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
python -m evals.wildguard.study freeze --selection /private/selection.json \
  --registry /private/registry.json --revisions evals/wildguard/revisions.json \
  --audit /private/wildguard-data/audit-budget.jsonl \
  --data-manifest /private/wildguard-data/manifest.json --out /private/freeze.json
python -m evals.wildguard.prepare_test --freeze /private/freeze.json --out /private/test
```

Set `HF_TOKEN` securely for the final command. Audit/test runs require `--freeze`; policy, model, source, settings and dataset provenance must match. Threshold calibration is a separate validation-only control, never part of the primary policy-only comparison.

The paper-ready evidence package will distinguish full datasets from budget samples, source-label ambiguity from model errors, and within-model tuning gains from cross-model comparisons. No article should claim a general advantage for policy tuning from a single public benchmark.
