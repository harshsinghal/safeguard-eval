# Malicious code and agent-skill screening: frozen evidence

This release compares six frozen models, two separately fine-tuned Liquid
classifiers (one per task), and two TF-IDF classifiers on code-file and skill
screening. The two tasks have separate leaderboards. The plan and selection
freeze precede final inference.

- [Readout](../../docs/malicious-artifacts/README.md) and [results](RESULTS.md).
- [Methods](../../docs/malicious-artifacts/METHODS.md), [plan](PLAN.md),
  [data audit](data-audit.json), [group overlap](group-overlap-audit.json).
- [Selection](freeze.json), [validation](validation-summary.json),
  [metrics and slices](results.json), [table](leaderboard.csv).
- [Costs](billing.json), [cleanup](cleanup.json),
  [independent metric check](independent-metric-check.json).
- [Reproduction instructions](../../docs/malicious-artifacts/RUNNING.md).

`predictions/` and `metadata/` contain IDs, labels, scores, hashes and provenance,
without artifact text. `policies/` contains the authored policies. `source/`
contains the registered implementation and reproduction tools. `learned/`
records trained-classifier selection and validation evidence; weights and
TF-IDF vocabularies remain private. `runtime/` records environments and timings;
these are not serving benchmarks. `amendments/` preserves the Unicode JSONL
reader correction and lossless checkpoint-storage amendment before final testing.

Upstream sources: [OMCBench](https://github.com/False-Positive-Community/open-malicious-code-benchmark)
and [MaliciousSkillBench](https://github.com/protectskills/MaliciousSkillBench).
Source revisions and public URLs are pinned in `source-manifest.json`. Raw
malicious archives and skill text are not redistributed. Third-party source
terms continue to apply; see the source repositories.

The code result is a derived file-level subset with largely model-assisted
labels. Skill evaluation holds out sources, not every structural family. All
models receive the same bounded text view; clipping can hide decisive evidence.
These are static classification results, not verification that execution is safe.

The exact input populations were restored and hash-verified. The public release
supports prediction/metric verification without models. Fresh training/inference
requires the recorded runtimes and restored inputs; the hosted Jev version is
recorded rather than downloadable. Reviewed papers, articles and the released
agent skill have not been automatically rewritten.
