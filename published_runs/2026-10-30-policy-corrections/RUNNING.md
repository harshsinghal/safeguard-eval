# Reproducing the policy-correction experiment

Start with the [registered protocol](PLAN.md). The published bundle contains
everything needed to reproduce metrics from saved scores without paid inference:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m evals.policy_corrections.study verify --state .
```

Use the bundle's pinned CPU requirements. The verification reselects policies
and cutoffs using validation only, then recomputes both final populations,
operating profiles, slices and paired bootstrap intervals. It does not tune on
test or require source text.

## Restore inputs for a new run

Use a new working directory and the recorded source snapshot or full repository.
Run the commands below from the repository root, or from the bundle's `source/`
directory. Restoring private input text additionally requires PyArrow (21.0.0
in the original preparation environment); the CPU
score-only verification above does not. Plotting additionally requires Matplotlib.
Copy `data-manifest.json`, `metadata/`, `policies/`, `authoring.json`,
`error-review.json`, `discovery-errors.jsonl.gz`, `discovery-summary.json` and
`prior-use-audit.json` into that directory. Obtain the pinned WildGuard Parquet
files through authorized dataset access. Their hashes are in the manifest.

```sh
python3 tools/restore_policy_corrections_inputs.py --state /absolute/path/state \
  --train /absolute/path/wildguard_train.parquet --test /absolute/path/wildguard_test.parquet \
  --stage development
python3 -m evals.policy_corrections.study register --state /absolute/path/state
```

The full-population assignments existed before this study. The prior-use census
excludes that preparation inventory and includes recorded experiment outputs and
references instead. The saved census, source hashes and exclusions explain the
new populations. Rerunning the census on a later repository will include this
newly completed experiment; use the frozen assignments for exact reproduction.

## Inference and staged selection

The original inference runtime is recorded in `runtime/correction-freeze.txt`.
It uses BF16, Python 3.12, Torch 2.8.0+cu128 and Transformers 5.10.2. Model
revisions and label-token IDs are saved with every output. Qwen thinking is
disabled. The supplied runtime scripts show the original commands and paths.

```sh
python -m evals.policy_corrections.infer --state /absolute/path/state \
  --model shieldstral --stage discovery-validation
python3 -m evals.policy_corrections.study select_shield --state /absolute/path/state
python -m evals.policy_corrections.infer --state /absolute/path/state \
  --model qwen --stage transfer-validation
python3 -m evals.policy_corrections.study freeze --state /absolute/path/state
```

Run selection on the pinned CPU environment. Record each freeze in version
control. The Qwen stage sees only the already selected revision and original
policy. The final freeze fixes both models' thresholds before final inputs are
restored or uploaded:

```sh
python3 tools/restore_policy_corrections_inputs.py --state /absolute/path/state \
  --train /absolute/path/wildguard_train.parquet --test /absolute/path/wildguard_test.parquet \
  --stage final
python -m evals.policy_corrections.infer --state /absolute/path/state --model shieldstral --stage final
python -m evals.policy_corrections.infer --state /absolute/path/state --model qwen --stage final
```

Collect all outputs and logs. Terminate paid compute, confirm termination and
reconcile billing before continuing the local analysis:

```sh
python3 -m evals.policy_corrections.study evaluate --state /absolute/path/state
python3 -m evals.policy_corrections.study verify --state /absolute/path/state
python3 tools/report_policy_corrections.py --state /absolute/path/state --out /absolute/path/RESULTS.md
python3 tools/plot_policy_corrections.py --state /absolute/path/state --out /absolute/path/figures
```

Plotting requires Matplotlib; figures do not affect predictions or selections.
Different hardware/library versions can change scores numerically. Keep source
prompts and provider credentials outside the repository. Never overwrite an old
freeze or completed output to make a new run appear identical.
