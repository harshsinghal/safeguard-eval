# Reproducing the representation experiment

The protocol is in [PLAN.md](PLAN.md). The two base models are frozen; logistic
regression is trained on labels. This first experiment covers WildGuard prompt
harmfulness only. It does not yet replicate on HateXplain.

## Prepare

From the repository root, reconstruct the pinned prompts from an authorized
WildGuardMix download and join them to the archived ensemble assignments. The
preparation command used in this study points to the existing private research
workspace; a new user must reconstruct those prompts from the original dataset,
preserving identifiers and SHA-256 values. No source prompts are published here.

To repeat fitting without the author's private workspace, create a fresh state
directory and copy only `metadata/`, `data-manifest.json` and `policy.json` from
the public bundle. Register the pinned source as described below. Keep old fits,
freeze and test results in the original bundle; new fitting creates its own
freeze before test extraction. Obtain
the authorized publisher files at dataset revision
`d29c47f41c8b51348b5c8e8c81c039b3132b66d1`:
[training Parquet](https://huggingface.co/datasets/allenai/wildguardmix/resolve/d29c47f41c8b51348b5c8e8c81c039b3132b66d1/train/wildguard_train.parquet)
and [test Parquet](https://huggingface.co/datasets/allenai/wildguardmix/resolve/d29c47f41c8b51348b5c8e8c81c039b3132b66d1/test/wildguard_test.parquet).
The restoration tool checks the original file, every text identity and label,
and the exact resulting input-file hash:

```sh
python3 tools/restore_activation_probe_inputs.py --state /absolute/path/probe-state \
  --source /absolute/path/wildguard_train.parquet --stage development
# After the pre-test freeze:
python3 tools/restore_activation_probe_inputs.py --state /absolute/path/probe-state \
  --source /absolute/path/wildguard_test.parquet --stage test
```

This utility additionally needs PyArrow. Keep original published results
immutable and do not commit restored inputs. To check saved metrics alone,
use the public bundle's README commands; no restoration or GPU is required.

```sh
python3 -m evals.activation_probe.prepare --state /absolute/path/probe-state \
  --prior-work /absolute/path/prior-research-work
python3 -m unittest tests.test_activation_probe -v
```

`data-manifest.json` pins populations and inputs. `inputs/` contains only each
example's identifier, text and text hash. `metadata/` contains labels for the
classifier stage. The feature extractor hashes metadata for alignment but does
not parse its labels. Keep both inputs and embeddings private: embeddings are
not guaranteed to conceal the text that produced them.

Before inference, write `registration.json` with `created_utc`, `sources` from
`evals.activation_probe.common.source_hashes()`, and `data_manifest_sha256`.
The extraction command refuses changed source files. Store any technical repair
as an explicit amendment before fitting rather than silently changing a run.

## Extract development features

Separate Python environments avoid incompatible Transformers requirements:

* PolicyLM: Python 3.12, torch 2.8.0, Transformers 4.57.6, huggingface_hub <1.
* Qwen: Python 3.12, torch 2.8.0, Transformers 5.10.2.
* Also install numpy, scipy, scikit-learn, accelerate, safetensors and threadpoolctl;
  Qwen additionally uses Pillow. Exact installed versions are saved with results.

```sh
python -m evals.activation_probe.extract --state /absolute/path/probe-state \
  --model policylm --stage development
python -m evals.activation_probe.extract --state /absolute/path/probe-state \
  --model qwen --stage development
```

These commands download pinned public model releases. They use GPU inference,
do not generate answers, and do not optimize language-model weights. The PolicyLM
hook preserves native score calculation and checks 16 fitting-only examples both
with and without hidden-state extraction. In this protocol each original message
has one feature row, even when the native helper creates multiple windows.

## Fit, freeze and test

Download development feature caches if fitting on a different machine. No GPU is
needed for linear classifier fitting. Test input files should remain off the
inference machine until `freeze.json` exists.

```sh
python3 -m evals.activation_probe.study train --state /absolute/path/probe-state
```

This saves all candidate fits and validation outputs, then freezes source/data
hashes, scaler statistics, coefficients, chosen representations and cutoffs.
Upload the freeze and test inputs, then extract test features in the corresponding
model environments:

```sh
python -m evals.activation_probe.extract --state /absolute/path/probe-state \
  --model policylm --stage test
python -m evals.activation_probe.extract --state /absolute/path/probe-state \
  --model qwen --stage test
python3 -m evals.activation_probe.study evaluate --state /absolute/path/probe-state
python3 -m evals.activation_probe.study reproduce --state /absolute/path/probe-state
python3 -m evals.activation_probe.study reproduce --state /absolute/path/probe-state --refit
```

Evaluation scores only configurations frozen on validation. The optional refit
requires private feature caches and repeats every candidate fit, checking its
validation probabilities. Published prompt-free outputs permit metric reproduction
without those caches. Coefficient files use NumPy arrays, not executable pickles.

## Compute lifecycle

The study uses GPU.ai with a three-hour provider termination timer and an hourly
price cap. This is an account of this experiment, not a recommendation or minimum
hardware requirement. A different provider, including RunPod, can host the same
jobs. Download artifacts, explicitly terminate the instance, verify termination,
remove temporary credentials, and reconcile billing. Do not leave the GPU running
while writing reports or performing optional CPU reproduction.
