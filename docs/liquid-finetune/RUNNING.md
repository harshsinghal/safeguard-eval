# Reproducing the Liquid fine-tune

The [plan](PLAN.md) is the specification. The fine-tuned model has a fixed binary
head: its score represents the learned WildGuard harmful-prompt label. It is
not a general-purpose policy interpreter, and it does not generate an answer.

## Verify the published numbers

Use a copy of the evidence bundle, since verification writes a fresh record:

```sh
python3 tools/verify_liquid_finetune.py --state /absolute/path/to/bundle-copy
```

This reselects all validation settings, checks every test confusion matrix and
metric, reproduces paired intervals and checks split integrity. It needs no GPU
or API key. It verifies recorded evidence; it does not rerun model fine-tuning.

## Reproduce training

Use the pinned model revision and the recorded GPU environment. Custom model
code is required; inspect it before enabling `trust_remote_code`. The provider's
[classification tutorial](https://github.com/Liquid4All/cookbook/tree/main/examples/lfm-encoder-classification)
explains the encoder-plus-head approach. Our binary head, search and experiment
controls are implemented in this repository rather than copied wholesale from
that tutorial.

Restore the source prompts from the pinned WildGuardMix dataset using the
published IDs/hashes; the [original restoration guide](../activation-probe/RUNNING.md)
describes the source parquet and row identities. `tools/restore_liquid_inputs.py`
restores this study's exact input files and checks their hashes. Keep the exact
input and metadata ordering. For a fresh replication, use the bundle's frozen
source snapshot and initialize a new directory containing only the protocol and
split identities, then restore the development texts:

```sh
python3 tools/restore_liquid_inputs.py \
  --state /absolute/path/new-state --protocol /absolute/path/published-bundle
python3 tools/restore_liquid_inputs.py \
  --state /absolute/path/new-state --source /absolute/path/train.parquet --stage development
```

The original preparation command instead reused our earlier private run and
checked all source file hashes:

```sh
python3 -m evals.liquid_finetune.prepare \
  --state /absolute/path/new-state \
  --previous /absolute/path/contrastive-heads-state
```

Only fitting and validation inputs/metadata are needed on the GPU initially.
Keep test text and labels out of the training environment. `registration.json`
records their expected hashes without requiring them to exist during training.

```sh
python3 -m evals.liquid_finetune.runner smoke --state /absolute/path/new-state
python3 -m evals.liquid_finetune.runner extract --state /absolute/path/new-state
python3 -m evals.liquid_finetune.runner train \
  --state /absolute/path/new-state --rate 0.00002 --seed 20261031
# Repeat for all six registered learning-rate/seed combinations.
```

Extracted features and validation histories can be copied to CPU for selection:

```sh
python3 -m evals.liquid_finetune.study prepare_selection --state /absolute/path/new-state
python3 -m evals.liquid_finetune.study freeze --state /absolute/path/new-state
python3 tools/verify_liquid_finetune.py --state /absolute/path/new-state --validation-only
```

Commit the freeze before moving test inputs to the GPU. Copy the freeze, frozen
head weights/scaler and validation selection record back to the GPU. Test labels
remain on CPU. Recheck all checkpoint hashes. The inference command reloads each
selected checkpoint and first verifies its validation scores:

```sh
python3 tools/restore_liquid_inputs.py \
  --state /absolute/path/new-state --source /absolute/path/test.parquet --stage test
python3 -m evals.liquid_finetune.runner test_inference --state /absolute/path/new-state
```

Collect selected weights, test scores, frozen test features and execution records.
Confirm the downloaded files match hashes, then terminate the GPU and reconcile
provider usage. Final labeled scoring is a CPU action:

```sh
python3 -m evals.liquid_finetune.study evaluate --state /absolute/path/new-state
python3 tools/verify_liquid_finetune.py --state /absolute/path/new-state
```

Large checkpoint weights, features and submitted prompt text are excluded from
Git. Published parameter hashes identify the exact checkpoints used. The
classification head is part of the saved state dictionary; weights from this
experiment must be loaded with the pinned backbone and pooling implementation.
Do not interpret a different quantized model or changed pooling as the same run.

The GPU training is not promised to be bit-identical on another hardware/software
stack. We record three training seeds and replay the saved checkpoints' validation
outputs. Exact numeric evidence verification uses the recorded CPU environment.
