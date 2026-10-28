# From learning to running a model

First separate two jobs. An **agent backend** such as Luna answers questions using
this skill. A **policy classifier** such as PolicyLM or Safeguard evaluates content
against a policy. Installing the skill loads guidance; it does not install or train
a classifier. An existing agent may have its own subscription or API costs.

## Choose a route for the task

| Route | Useful starting point | What still needs checking |
|---|---|---|
| Local inference | A small learning experiment on hardware the user owns | Available RAM and disk, exact runtime support, quantization, prompt format, labels, context and speed |
| Hosted inference API | Trying a supported checkpoint without managing a server | Exact model ID, custom-policy support, pricing, limits, errors, data terms and availability |
| Rented GPU | Running an open checkpoint's native implementation | Total model memory, runtime dependencies, startup time, hourly and storage charges, teardown verification |

Use the user's stated model or environment. If unknown, explain these routes
briefly and ask for the machine or deployment constraint only when needed. Avoid
rankings of GPU providers. No provider in this guide is endorsed.

## What we tried locally

On 28 October 2026 we ran **Ollama 0.32.5, Qwen3.5:2b, Q8_0** on an Apple Silicon
Mac with 16 GiB of unified memory. The local download reported about 2.68 GB. We
used a system policy, separate user content, structured JSON labels, temperature
zero, thinking disabled, and a 4,096-token context. The policy distinguished
threats from criticism, fiction, and reporting abuse.

All eight handwritten teaching cases returned parseable JSON. **Only four matched
their intended labels: the model blocked all eight, including all four allowed
cases.** One explanation described a non-threat while its label still said BLOCK.
This established that the local integration ran; it did not establish a useful
moderation classifier. A valid JSON response is not necessarily the right decision.
The model was unloaded after the test. There was no inference-provider bill;
electricity and machine costs were not measured. See source `local-ollama-smoke`
and `local-running-readout` in [sources.json](sources.json).

This was one pass over eight original English examples, with no reserved test set,
no policy search, and no specialist comparison. It is not a rerun of the WildGuard
or HateXplain benchmarks. Do not present 4/8 as a general Qwen performance estimate.
We have not tested PolicyLM, Shieldstral, CoPE, or Safeguard on Ollama on this Mac.

To reproduce the integration check in a repository checkout, use source
`ollama-smoke-runner`. It requires an already installed model and writes a new
result file; it does not download weights. The tested setup commands were:

```bash
# After checking free disk and RAM; downloading weights needs network access
ollama pull qwen3.5:2b
python3 tools/ollama_policy_smoke.py --output work/my-local-smoke.json
```

The runner records the resolved model digest, format, settings, raw answers,
durations, token counters, errors, and whether unloading succeeded. Check the
model digest when reproducing: tags and runtime behavior can change. Inspect
allowed and prohibited cases before moving to a larger evaluation.

## Ollama support is checkpoint-specific

Ollama's [Safeguard library](https://ollama.com/library/gpt-oss-safeguard) lists
20B and 120B variants. At the check date the 20B download was about 14 GB. We did
not download it because this Mac had only about 16 GB of free disk and 16 GiB of
unified memory. A provider statement about fitting in 16 GB of GPU VRAM is not a
guarantee of comfortable operation on a 16 GiB Mac sharing memory with the OS.

For a supported checkpoint, use the runtime's chat template and the publisher's
policy roles. The [Ollama chat API](https://docs.ollama.com/api/chat) supports
structured outputs and explicit model unloading. Set and record context and
thinking options where supported. Test errors and malformed output as well as
valid decisions. Quantization or a different template can change behavior.

PolicyLM's native category/scoring interface is not equivalent to an arbitrary
GGUF chat conversion. Follow its [model card](https://huggingface.co/musubilabs/policylm-1.7b)
and supported library. Do not claim that every open checkpoint runs in Ollama or
that an unofficial conversion preserves the benchmark adapter. See [models.md](models.md).

## Hosted endpoints: verify the exact name

[Groq documents `openai/gpt-oss-safeguard-20b`](https://console.groq.com/docs/model/openai/gpt-oss-safeguard-20b).
It was listed as a preview model when checked. The project's original demo used
Groq; Groq is different from xAI's Grok. Recheck availability and data terms before
a new integration. Provider throughput advertising does not measure our workflow's
latency, especially with long policies, queues, reasoning, and parsing retries.

The [Cerebras shared-model catalog](https://inference-docs.cerebras.ai/models/overview)
listed `gpt-oss-120b` and `qwen-3.8-27b` when checked; it did **not** establish a
shared GPT-OSS **Safeguard** endpoint. Ordinary GPT-OSS and Safeguard are different
checkpoints. Dedicated or account-specific offerings require separate verification.
Do not promise Safeguard availability there based on a similar model name.

OpenRouter can be a backend for an agent: our Pi user test uses
[`openai/gpt-6-luna`](https://openrouter.ai/openai/gpt-6-luna). That test measures
the skill-assisted conversation, not Luna's moderation accuracy. Search the
current catalog for each requested classifier rather than assuming our tested
panel is served by every inference provider. An API's moderation, retention, or
zero-retention settings must be verified for the exact route and account.

## Renting GPUs without endorsing a provider

Harsh Singhal's completed GPU experiments in the archived studies used **GPU.ai**.
**Runpod** was available as a fallback; those records do not establish a completed
Runpod benchmark run. These are historical setup facts, not quality comparisons
or recommendations. Users should research providers, terms, hardware, regions,
availability, and pricing themselves. Follow current provider documentation.

Before an authorized run, agree on a spending ceiling and a stop time. Estimate
setup, model download, inference, idle time, persistent disks, and egress where
applicable. Keep API keys in a secret store or environment; never paste them into
the policy, transcript, committed code, or a public result. Giving an agent a
provider key can enable billable actions; possessing a key alone is not permission
to launch an unlimited experiment.

Use an execution plan with cleanup on success, failure, and interruption. Record
resource IDs privately, then **terminate the rented instance and verify its state**.
Stopping inference or disconnecting SSH may leave the GPU bill running. Check
whether attached volumes or other resources continue billing; remove only resources
within the agreed scope. Report unresolved cleanup immediately.

Always finish with usage: provider and exact model, hardware, requests, tokens when
available, runtime, failed calls, cost and its source, and confirmed cleanup state.
If billing is delayed or unknown, report that explicitly rather than claiming $0.
For local runs, report runtime and token counts and distinguish no provider charge
from no compute cost. Do not promise that a smaller model is cheaper or faster
without measuring the intended deployment and error trade-offs.

Primary-source availability statements above were checked on 28 October 2026.
The [external catalog](external-sources.json) separates these live sources from
the pinned experiment records.
