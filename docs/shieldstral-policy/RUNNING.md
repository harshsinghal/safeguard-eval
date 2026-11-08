# Run the Shieldstral moderation adaptation pilot

Run from the repository root. The [registered plan](PLAN.md) defines the
interventions, selection, resource limits and interpretation. Use Python
3.12, CUDA-enabled Torch 2.8.0+cu128, Transformers 5.10.2, PEFT 0.21.2 and
a CUDA GPU with BF16 support. Hugging Face Hub 1.33.0 was used to load the
pinned Transformers-format weights. Keep all private data and weights in
ignored work storage.

Restore the original fit, validation, and protected evaluation files with
the [Liquid router restoration steps](../liquid-router/RUNNING.md). The
Shieldstral study reads the Liquid registration, data and public metadata.
It uses the original ALLOW/BLOCK labels and the fixed enterprise policy
catalog.

Cache the pinned Shieldstral revision with only the Transformers-format
weight file. The publisher also supplies a redundant Mistral-format weight
file.

```sh
hf download mistralai/Shieldstral-1.0-3B \
  --revision 003ec7e2b0bab5f0e6307edbaf186fa5822b76f5 \
  --exclude consolidated.safetensors
```

Choose a new ignored state directory to repeat the experiment. A stage
refuses to overwrite existing outputs. After a failed attempt preserve its
logs and outputs under a separate name before retrying.

```sh
source_state=work/liquid-router-v0
shield_state=work/shieldstral-policy-v1

timeout 35m python -Bu -m evals.shieldstral_policy.smoke "$source_state" "$shield_state/smoke"
python -Bu -m evals.shieldstral_policy.data "$source_state" "$shield_state"
timeout 36m python -Bu -m evals.shieldstral_policy.study develop "$shield_state"
timeout 36m python -Bu -m evals.shieldstral_policy.study evaluate "$shield_state" --source "$source_state"
python -Bu -m evals.shieldstral_policy.analysis "$shield_state" "$shield_state/results.json"
```

Development writes the two local PEFT adapters and `freeze.json`.
Evaluation verifies the freeze, development predictions, and checkpoint
hashes before loading final documents. The group-bootstrap confidence intervals
require NumPy. Recompute the published scorecard without model access using
the [offline verifier](../../tools/verify_shieldstral_policy.py).

To load a fitted adapter in the same local environment, instantiate
`evals.shieldstral_policy.runtime.load_base()` and then call
`peft.PeftModel.from_pretrained(base, adapter_directory).eval()`.
Use the same renderer, canonical yes/no scoring and frozen cutoff to
reproduce the registered decisions.
