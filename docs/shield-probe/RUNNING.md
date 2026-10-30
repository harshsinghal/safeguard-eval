# Reproducing the Shieldstral representation comparison

The [registered protocol](PLAN.md) fixes models, policy, populations, candidate
fits and selection rules. Language-model weights are frozen; the small regression
heads are trained with labels. Do not treat this as training-free moderation.

## Inputs and registration

Use an independent working state outside the tracked repository. The original
preparation command reconstructs the existing research workspace:

```sh
python3 -m evals.shield_probe.prepare --state /absolute/path/state \
  --prior-work /absolute/path/research-work
```

For a portable rerun, copy `metadata/`, `data-manifest.json` and `policy.json`
from the published study into a new state and restore authorized source text
using the earlier [input restoration instructions](../activation-probe/RUNNING.md).
Run `tools/restore_shield_probe_inputs.py` with `--state`, `--source` and
`--stage development` (or `--stage test` after freezing). The populations and
input-file hashes are identical to that study. Keep text and
embeddings private. Register `created_utc`, `sources` from
`evals.shield_probe.common.source_hashes()`, and `data_manifest_sha256` in a fresh
`registration.json`. Extraction rejects changed source and input hashes.

## Frozen feature extraction

The recorded GPU environment and exact dependency versions accompany the results.
The extraction runtime used Python 3.12, Torch 2.8.0, Transformers 5.10.2, NumPy,
SciPy, scikit-learn, threadpoolctl, accelerate, safetensors, Pillow and
mistral-common. Download only the pinned model revisions specified in the protocol.

```sh
python -m evals.shield_probe.extract --state /absolute/path/state \
  --model shieldstral --stage development
python -m evals.shield_probe.extract --state /absolute/path/state \
  --model qwen --stage development
```

Only label-free fitting and validation inputs go to the GPU initially. Each
extractor checks native score parity on 16 fitting examples and saves token IDs,
representation hashes, runtime records and memory measurements. The full
development outputs must pass shape, finite-value, identity and hash checks.

## Training and pre-test freeze

```sh
python3 -m evals.shield_probe.study train --state /absolute/path/state
```

The original fitting ran locally on CPU with Python 3.9, NumPy 2.0.2,
SciPy 1.13.1 and scikit-learn 1.6.1. Match the bundle's `requirements.txt` and
`runtime/cpu-environment.json` for coefficient reproduction; the GPU extraction
environment's scikit-learn version was not used to fit these classifiers.

This fits scaling and coefficients only on fitting rows and selects regularization,
representations and cutoffs on validation. It writes all candidates and a freeze.
Record that freeze in version control before uploading any test inputs. A
technical repair requires an explicit amendment; do not silently change frozen
code or overwrite a completed extraction or result.

```sh
python -m evals.shield_probe.extract --state /absolute/path/state \
  --model shieldstral --stage test
python -m evals.shield_probe.extract --state /absolute/path/state \
  --model qwen --stage test
python3 -m evals.shield_probe.study evaluate --state /absolute/path/state
python3 -m evals.shield_probe.study reproduce --state /absolute/path/state
python3 tools/verify_shield_probe.py --state /absolute/path/state
```

Test evaluation scores only frozen choices. Cached development representations
allow a full CPU refit with `study reproduce --refit`; this compares coefficient
arrays exactly and validation scores to a numerical tolerance. Saved predictions
allow metric reproduction without accessing prompts or paying for another GPU.

Generate human-readable results and the recorded extraction summary with:

```sh
python3 tools/report_shield_probe.py --state /absolute/path/state --out /absolute/path/RESULTS.md
python3 tools/summarize_shield_probe_runtime.py --state /absolute/path/state
python3 tools/plot_shield_probe.py --state /absolute/path/state --out /absolute/path/figures
```

Plotting additionally requires Matplotlib. The original plot used the local
Python 3.11 plotting environment; it does not change predictions or selections.

Always download artifacts, terminate paid compute, confirm termination, remove
temporary credentials and reconcile billing. The current experiment retains the
same cumulative budget as earlier studies; changing providers does not reset it.
