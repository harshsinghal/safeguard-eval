# Running the competence router locally

Use the existing native guard environments and pinned model caches described in
[the routed system guide](../routed-guard/RUNNING.md). No new model download or
serving-engine migration is required. Set `HF_HUB_OFFLINE=1`,
`OPENBLAS_NUM_THREADS=4` and `OMP_NUM_THREADS=4`. Use the shared Python environment
with Torch, Transformers, scikit-learn, FastAPI, and the existing pinned adapters.
The PolicyLM worker still needs its separate Transformers 4.57.6 interpreter.

All paths in the commands below are user-supplied local paths. `work/` is ignored
by Git. Inputs and checkpoints stay there; only prompt-free evidence belongs in
the repository. Prompt-free evidence is published under `local_runs/competence-router-v0`.

```bash
python -B -m unittest tests.test_competence_router tests.test_routed_guard -v
python -B -m evals.competence_router.study prepare \
  --state work/competence-router-v0 \
  --liquid /path/to/liquid-router-v0 \
  --pilot /path/to/routed-guard-pilot \
  --pool /path/to/enterprise-benchmark/pool.jsonl
python -B -m evals.competence_router.study extract --state work/competence-router-v0
python -B -m evals.competence_router.study collect --state work/competence-router-v0 --split fit
python -B -m evals.competence_router.study collect --state work/competence-router-v0 --split validation
python -B -m evals.competence_router.study fit --state work/competence-router-v0
# The fit step freezes the checkpoint and selection before test outcomes.
python -B -m evals.competence_router.study collect --state work/competence-router-v0 --split test
python -B -m evals.competence_router.study evaluate \
  --state work/competence-router-v0 --pilot /path/to/routed-guard-pilot
python -B -m evals.competence_router.study actual --state work/competence-router-v0
```

Preparation verifies source and adapter hashes and registers model/data/code
versions before collecting new outcomes. Interrupted guard collection resumes
completed bound predictions. Preserve failed attempts. Changing registered code
requires a documented amendment or a new state; never replace old results.
Feature extraction may run alongside fitting-outcome collection because it never
reads guard outputs or labels. It processes the held-out *inputs* only to check
bounded-view collisions; all scaler/head parameters use fitting data only.

For offline CPU routing:

```python
from evals.competence_router.model import CompetenceRouter
from evals.routed_guard.common import read, labels_for
router = CompetenceRouter('work/competence-router-v0/checkpoint', threads=4)
policies = read('benchmarks/enterprise-moderation/v0.1/policies.json')
policy_id = 'source_code-v0'  # Trusted application configuration, never inferred.
result = router.predict('def add(a, b): return a + b',
                        policies[policy_id], labels_for(policy_id))
print(result['selected_model'], result['guard_correctness_probabilities'])
# This is a routing result. It never grants ALLOW or skips the guard.
```

To serve after the study completes:

```bash
python -B -m evals.competence_router.server \
  --config work/competence-router-v0/config.private.json --port 8766
```

`POST /v1/moderate` accepts `content`, trusted `policy_id`, and optional opaque
`request_id`. Every request attempts the selected guard, then Clef on primary
backend failure. Router errors use Clef directly. Unresolved backend failures
return REVIEW with `status=error`, which counts as incorrect in evaluation.
`POST /v1/guard` is the forced-model control endpoint; `POST /v1/unload` removes
the active guard. The gateway supports one GPU guard worker at a time. Native
BF16 weights for all four guards do not fit simultaneously with normal headroom.
The study's actual-evaluation command stops its own gateway and unloads workers.

This checkpoint is deliberately FP32 on CPU. Its four output probabilities are
independent correctness estimates and do not sum to one. The policy text and
allowed decisions form the supported-policy contract; editing the policy falls
back to Clef until independently validated. Guard weight/adapter changes require
new competence labels and evaluation. Dynamic INT8 needs its own measured study.
