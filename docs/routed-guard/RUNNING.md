# Run the routed guard service

The gateway runs the frozen Liquid 350M router on CPU and maintains at most one
GPU guard worker. Every accepted moderation request invokes a guard. Low router
confidence, missing category mappings and router errors select a default guard.
Backend failures attempt that default when different; unresolved calls return
operational REVIEW with error status and earn no accuracy credit.

## Models and runtimes

| Logical model | Native interface | Initial runtime |
|---|---|---|
| policylm | Policy categories and scores | Transformers 4.57.6 in an isolated environment |
| shieldstral | Native yes/no criterion scoring | Transformers 5.10.2 |
| kev | Pinned base + LoRA + pointer head | Transformers 5.10.2, PEFT, reference kernels |
| clef | Backbone + joint schema head | Transformers 5.10.2, reference kernels |

The native heads are part of each classifier. Ordinary chat generation does not
replace Kev or Clef scoring. The repository's earlier serving study used vLLM
for Shieldstral and native servers for the other three. This first local routing
pilot uses native reference implementations for all four; no local vLLM speed
or parity result is claimed. A backend can later move behind an external serving
engine if it preserves the same model/head/policy/decision contract.

Four simultaneous BF16 copies require roughly 35GB for weights before runtime
memory, exceeding this 32GB 5090. The gateway therefore loads guard workers on
demand and unloads the previous worker before starting another. This allows
inference against every registered model but adds cold-start latency when the
route changes. Models remain cached on local disk. Other applications' processes
are left alone. A multi-GPU or separately validated quantized serving profile
would be a different deployment experiment.

## Environment and assets

Use Python 3.12, Torch 2.8.0 with CUDA 12.8, Transformers 5.10.2, FastAPI 0.162.0,
Uvicorn 0.54.0, PEFT 0.21.2, Torchvision 0.23.0 matching Torch/CUDA, and the dependencies of the existing Liquid router.
PolicyLM requires Transformers 4.57.6 and huggingface-hub 0.36.2 in a separate
interpreter. Its environment can reuse the local Torch installation; private
interpreter paths stay in ignored work/. The other three workers use the
gateway's interpreter. No paid provider or external inference API is required.

```bash
python -B tools/download_routed_guard_models.py
python -B -m evals.decision_models.fetch_sources --destination work/decision-vendor
```

The downloader pins the four model releases and Kev's base. It excludes duplicate
consolidated/GGUF artifacts. Vendor source files are verified against the existing
SHA256 manifest before execution. Raw source code and skill examples are always
inert classifier input, never installed or executed. Restore the fixed enterprise
suite inputs using that benchmark's instructions. Restore the locally trained
Liquid classifier checkpoint using its inference instructions.

## Prepare, check, select and evaluate

Use a new state directory for a new pilot. The fixed benchmark is unchanged.
The preparer selects eight evaluation cases per task by stable stratified hash
and retains all 192 calibration cases, with exact input and policy bindings.

```bash
python -B -m evals.routed_guard.experiment prepare \
  --state work/routed-guard-pilot \
  --inputs work/frozen-enterprise-inputs-v0.1 \
  --checkpoint work/liquid-router-v0/checkpoints/epoch-1 \
  --vendor work/decision-vendor \
  --policy-python work/policyenv/bin/python
python -B -m evals.routed_guard.experiment smoke --state work/routed-guard-pilot --model shieldstral
python -B -m evals.routed_guard.experiment smoke --state work/routed-guard-pilot --model policylm
python -B -m evals.routed_guard.experiment smoke --state work/routed-guard-pilot --model kev
python -B -m evals.routed_guard.experiment smoke --state work/routed-guard-pilot --model clef
python -B -m evals.routed_guard.experiment register --state work/routed-guard-pilot
python -B -m evals.routed_guard.experiment calibrate --state work/routed-guard-pilot
python -B -m evals.routed_guard.experiment test --state work/routed-guard-pilot
python -B -m evals.routed_guard.experiment stop --state work/routed-guard-pilot --keep-gateway
```

Calibration can collect an explicit subset with `--models policylm,shieldstral,kev`,
then collect the remainder later. It uses one shared 90-minute phase budget.
The category mapping is frozen only after all four have complete calibration
outputs. Selection uses class-balanced accuracy with equal task influence among
available calibration tasks. NotInject and JBB have no calibration cases. The
default guard is the strongest calibration selection across all available tasks.
Model ties use the predeclared order in the plan. Pilot results cannot replace
those choices. `test` refuses an unfrozen mapping or changed registration.

Each pilot case receives four fresh single-model controls and a fresh actual
classifier-to-guard HTTP request. Requests are grouped by predicted destination
to amortize worker loading; classification runs again inside each real request.
Recorded client latency includes HTTP, queueing, CPU routing, any model load,
native inference and deliberate GPU cooldown. This is a serial grouped pilot,
not a production arrival-rate or simultaneous-residency benchmark.

## Call the service

The launcher prints its localhost URL and stores it in
`work/routed-guard-pilot/gateway.private.json`. The CPU gateway may remain ready
with no GPU worker resident after the pilot. A subsequent request starts the
required GPU worker. Reuse a state only for its registered experiment.

```python
import json
from pathlib import Path
from urllib.request import Request, urlopen

state = Path("work/routed-guard-pilot")
base = json.loads((state / "gateway.private.json").read_text())["base"]
body = {"content": "Please summarize the quarterly report.",
        "policy_id": "harmful_requests-v0"}
request = Request(base + "/v1/moderate", data=json.dumps(body).encode(),
                  headers={"Content-Type": "application/json"})
with urlopen(request, timeout=480) as response:
    print(json.load(response))
```

`GET /v1/models` lists the logical model catalog and active worker.
`POST /v1/moderate` runs CPU classification and guard dispatch.
`POST /v1/guard` directly evaluates a specified model for controls; add
`"model": "kev"`, `"clef"`, `"policylm"`, or `"shieldstral"` to the request.
`POST /v1/unload` unloads the active GPU worker. Services bind to loopback only.

The caller supplies a trusted policy ID from the registered catalog. The
classifier receives text only; it does not receive policy IDs, benchmark/task
labels or source metadata as routing hints. Policy selection is independent of
the predicted category. Guard input remains complete even when the CPU router
uses its bounded 256-token view. Context overflow is an explicit failure, never
silent truncation or ALLOW.

For binary policies guards retain ALLOW/BLOCK choices even if a source stress
panel contains only one reference class. For custom-policy and injection-context
tracks, PolicyLM and Shieldstral use explicit BLOCK/REVIEW criterion wrappers
with BLOCK precedence, while Kev and Clef use native three-option Choice. These
wrappers are new configured systems and are recorded separately from old studies.

Stop the gateway and unload its worker with the same `stop` command without
`--keep-gateway`. Worker logs, process receipts, private paths, prompts, weights
and config remain ignored. Safe public records include model revisions, hashes,
classification traces, decisions, metrics, preflight outcomes and sampled
resource records. Software operation duty is capped by idle time at a nominal
20%; clocks/voltage/hardware power limits are unchanged.

## Reproduce public scores without model inference

```bash
python -B tools/verify_routed_guard_evidence.py --archive published_runs/2026-11-05-routed-guard-pilot
```

The verifier checks archive hashes, recomputes the calibration mapping, scores
the single-model controls and routed system, and validates that every successful
response follows the frozen route and records a guard invocation. It requires
no source prompts, model weights, GPU or API credentials. Native call counts
refer to wrapper invocations; native windowing can perform multiple forwards.
