# Running the released decision heads

These experiments use the publishers' existing checkpoints. They do not train
weights. The policies and decision cutoffs are the things we optimize.

## The interface matters

Both models accept a state and typed questions. Our request has one question:

```json
{
  "state": {"content": "The text to moderate"},
  "questions": {
    "moderation": {
      "type": "choice",
      "instructions": "Apply the policy to the submitted text.",
      "criteria": {
        "ALLOW": "The policy's definition of compliant content",
        "BLOCK": "The policy's definition of a violation"
      }
    }
  }
}
```

The two adapters preserve this meaning but serialize it using each model's
native code. Kev uses its released pointer head; Clef uses the release's joint
schema head. Neither adapter generates a text answer. Loading only a Qwen
backbone in a chat server would bypass the head that this experiment evaluates.
We have not tested these classifiers through Ollama or GGUF conversions.

The wrapper passes no benchmark label, rationale, row identifier, or source
category to the model. It keeps independent examples in separate requests, even
when several requests are processed as a tensor batch. It retains full-precision
probabilities before the providers' public response helpers round them.

Kev's returned logits already include its released temperature scaling. Our
wrapper does not fit another temperature. Clef's returned logits are its native
head output, with no extra temperature transformation in our wrapper. Choosing
a BLOCK cutoff on validation changes the final decision rule; it does not
establish that the probabilities are calibrated.

## Repeating the inference

The [plan](PLAN.md) specifies the dataset hashes, candidate budget, selection
rules, and context limit. The run archive records exact installed dependencies.
This study uses separate Python 3.12 environments:

* Kev: Torch 2.8.0, Transformers 5.17.0, PEFT 0.21.2, Pydantic 2.12.3.
* Clef: Torch 2.11.0, Torchvision 0.26.0, Transformers 5.10.2.

Both also need Hugging Face Hub, Safetensors, Accelerate, NumPy, SciPy, and
scikit-learn. Use the archived environment manifests rather than assuming newer
versions are equivalent. BF16 is used for both backbones. Kev's model card also
reports an FP32 reference evaluation path, which this run does not reproduce.

Fetch and inspect the pinned publisher code:

```sh
python -m evals.decision_models.fetch_sources --destination /absolute/path/vendor
```

Prepare the existing canonical Jev dataset files, then register the study:

```sh
python -m evals.decision_models.study prepare \
  --data /absolute/path/canonical-data --state /absolute/path/state
```

The data directory contains `wildguard` and `hatexplain`, each with the original
`fit.jsonl`, `validation.jsonl`, and `test.jsonl` files. Registration refuses
changed populations. Review the source benchmarks' licenses before reuse.

In each model's environment, run its development stage:

```sh
python -m evals.decision_models.infer \
  --state /absolute/path/state --vendor /absolute/path/vendor \
  --model kev --stage development
```

Repeat for `--model clef` in the Clef environment. Development evaluates brief
and detailed fitting policies, derives the four-example candidate from fitting
errors, then evaluates all three policies on validation. Freeze both models'
selections before running either test stage:

```sh
python -m evals.decision_models.study freeze --state /absolute/path/state
python -m evals.decision_models.infer \
  --state /absolute/path/state --vendor /absolute/path/vendor \
  --model kev --stage test
```

Repeat the test command for Clef. Keep test files off the inference machine until
the freeze if using a remote host, as this study does. Resume commands validate
policy and content hashes. Full inputs exceeding the registered context limit
remain unresolved errors; they are not silently clipped or excluded.

The study uses one rented 48GB RTX6000 Ada GPU from GPU.ai. This is a record of
the deployment, not a provider endorsement or a minimum-memory claim. RunPod
remains an available fallback but is not needed if this rental completes.
Users should select their own provider, set a spending cap and automatic
termination, reconcile actual charges, and verify that resources are terminated.
