# Reproduction and progress

## Progress

- [x] Pin sources and official model checkpoints.
- [x] Audit eligibility, exact/near duplicates, template and author grouping.
- [x] Implement native interfaces, paired input views and learned controls.
- [x] Check input/cache contracts and label-free model payloads.
- [x] Publish registration and pre-test runtime/data amendments.
- [x] Complete validation within the existing $6 cap.
- [x] Publish validation selection before test inference.
- [x] Run test, independently check metrics, publish failures and limits.
- [x] Reconcile provider/API charges; verify resource termination.

## Completed verification

All 50 final arms passed independent confusion-count and metric checks, including
companion-file subsets and repeat controls. The 16 decoder label-contract checks
all returned expected label tokens. Identical single-file inputs produced identical
Jina embeddings. Seven local contract tests pass. Final GPU/API cost is
$2.115403262; provider termination and temporary-key removal are confirmed.

## Local verification

Use Python 3.12 with numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1 and joblib.

```sh
python -m unittest evals.cyber_skill_guardrails.test_contracts
python -m evals.cyber_skill_guardrails.report --state RUN_DIRECTORY --public
```

The second command requires the final public prediction bundle. Public reproduction
does not require raw benchmark text, model downloads or an API key.

To restore inference inputs, check out the two upstream revisions in PLAN.md.
Save the [MITRE source JSON](https://github.com/meta-llama/PurpleLlama/blob/f64eebd53003a87d9c2d2a3a712133534c214c8d/CybersecurityBenchmarks/datasets/mitre/mitre_benchmark_100_per_category_with_augmentation.json)
as mitre.json and the [FRR source JSON](https://github.com/meta-llama/PurpleLlama/blob/f64eebd53003a87d9c2d2a3a712133534c214c8d/CybersecurityBenchmarks/datasets/mitre_frr/mitre_frr.json)
as frr.json in a private directory. The primary study reads MITRE's base_prompt
field from that file. Clone MalSkillBench without installing anything. Keep the public
registration, metadata and package manifest in RUN_DIRECTORY, then run:

```sh
python -m evals.cyber_skill_guardrails.restore --state RUN_DIRECTORY \
  --checkout MALSKILLBENCH_CHECKOUT --cyber-sources PRIVATE_CYBER_DIRECTORY
```

Restoration checks every package Git blob and every final input hash. Respect the
upstream license; raw skill text and model weights are excluded from this repository.

Paid reruns require a new explicit budget. Use provider termination limits, log
unknown API charges conservatively, and stop resources after collecting evidence.
Models use separate compatible environments; dependency snapshots accompany results.

The public runtime recipes use a Linux CUDA host and absolute paths from this
study. Adapt those paths in a fresh run directory, obtain access to gated model
repositories through your own account, and supply credentials through private
environment variables or files. Do not commit credentials. The decision-model
adapters also require the provider reference code at the revisions and hashes
recorded in the archived source. Jev uses an external API; its private responses
and billing database are separate from the public prediction summary.

A full rerun needs its own output directory, spending ledger and selection freeze.
Do not overwrite the archived study or assume recomputed features and learned
weights will have identical hashes on another runtime. Public metric reproduction
uses recorded predictions and requires no inference.
