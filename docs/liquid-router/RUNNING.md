# Run the Liquid CPU classifier

Run from the repository root. The local experiment uses Python 3.12 and the
versions in `requirements.txt`. Install PyTorch's CPU wheel for deployment, or
the CUDA 12.8 wheel for the optional local fitting step. No paid service is used.

## Restore and fit

The base model is `LiquidAI/LFM2.5-Encoder-350M`, pinned to
`b886781f7c6f10ca9b7096e21b83e30a073c2f39`. Download it with
`huggingface_hub.snapshot_download` before fitting. The original masked-LM
wrapper must load without missing, unexpected, or mismatched weights; then the
runner extracts the pretrained encoder body. A direct encoder load of this
original checkpoint is incompatible with the registered Transformers version.

Restore sources privately using the fixed benchmark's instructions. Authorized
WildGuard access can be supplied through `HF_TOKEN_FILE`; never place tokens in
commands, output, or Git. Code archives and skill text are read as inert data.

```bash
python -B -m evals.enterprise_benchmark.sources --state work/enterprise-benchmark
python -B -m evals.liquid_router.prepare --state work/liquid-router-v0 --existing work/enterprise-benchmark
python -B tools/verify_liquid_router_inputs.py --state work/liquid-router-v0
python -B -m evals.liquid_router.study train --state work/liquid-router-v0
python -B -m evals.liquid_router.study evaluate --state work/liquid-router-v0 --precision fp32
python -B -m evals.liquid_router.study evaluate --state work/liquid-router-v0 --precision int8
python -B tools/report_liquid_router.py --state work/liquid-router-v0
```

Choose a new state directory for a new experiment. Existing registrations,
freezes and completed CPU evaluations cannot be silently overwritten. Fitting
checks registered source and data hashes. Final evaluation also verifies the
selected checkpoint hashes. The runner never reads test inputs during training.

## CPU inference

The checkpoint bundles encoder weights, pinned model code, tokenizer, head,
category order, bounded-view settings and validation-selected routing settings.
After restoring that local directory, inference needs no network access or GPU.

```python
import json
from pathlib import Path
from evals.liquid_router.model import Router

state = Path("work/liquid-router-v0")
freeze = json.loads((state / "freeze.json").read_text())
router = Router(state / freeze["checkpoint"], threads=4, int8=True)
result = router.predict("Explain how to configure a secure firewall.")
print(result)
```

Keep one Router instance resident across requests; construction loads and
optionally quantizes the model. FP32 is available with `int8=False`. Dynamic
INT8 quantizes linear layers; embeddings, convolution and other operations keep
their original precision. This is not a fully integer model or a GGUF runtime.

`candidate_categories` identifies safety checks to consider. The scores estimate
a reference benchmark family, not the probability of harm. `fallback_required`
requests a general check when confidence is low. It is not a reliable detector
of every unfamiliar category. `moderation_decision` is always null. The caller
must still invoke the selected guard(s) with the relevant policy and context.
No guard-model assignment has been selected or deployed by this experiment.

Inputs above 256 tokens use first 96, middle 64 and last 96 tokens. The response
reports original/used token counts and truncation. This is a measured routing
compromise; it cannot establish safety for omitted material. Inputs must be
nonempty UTF-8 text no larger than one MiB.

## Interpretation

Seven category names denote checks: agent behavior, source-code artifacts,
cybersecurity requests, general request harmfulness, hate speech, prompt
injection, and skill artifacts. Multiple benchmark tasks pool into these
categories. Each training example has one benchmark-family reference; other
applicable categories have not been exhaustively annotated. Multiple returned
candidates are alternative routes, not validated semantic multilabel outputs.

The 48 custom-policy test items are an unsupported-category diagnostic and are
excluded explicitly from the seven-category quality headline. All 983 fixed
suite cases remain intact. Other held-out-source diagnostics include benign
injection lookalikes, jailbreak attempts, synthetic injection context and full
skill packages. Original task labels and model rankings remain unchanged.

## Local resource limits

Training uses microbatch one, four CPU threads, a 20% software operation-duty
target and a 45-minute bounded fitting schedule. A background monitor samples
GPU temperature/power/utilization/memory every half second; cooldown begins
above 60C or 180W and a stop occurs at 70C or sustained samples above 250W.
Software idle time cannot guarantee an instantaneous watt limit. Hardware
clocks, voltage and power limits are unchanged. CPU evaluations run serially
with four threads and batch one; report cold load separately from warm latency.

Source text, trained weights, temporary portable smoke checkpoints, features
and the fitted text-control model stay in ignored `work/`. Public artifacts
contain metadata, hashes, predictions, metrics and resource records only.

## Reproduce the public evidence without inference

```bash
python -B tools/verify_liquid_router_evidence.py --out work/liquid-router-evidence-check
```

This verifies archived SHA256 hashes, decompresses metadata and predictions,
and reproduces the paired CPU precision comparison and grouped intervals.
It needs no prompts, checkpoint, GPU, Hugging Face access or API credentials.
