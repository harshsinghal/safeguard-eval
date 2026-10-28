# Local running and agent-experience checks

These checks answer two different questions. The Ollama test asks whether a small
local model can execute a policy-classification request, and what goes wrong.
The Pi test asks whether an ordinary user can learn from an installed skill using
a lower-cost backend. Neither is an extension of the moderation benchmark results.

## Ollama: execution worked; the labels were not reliable

We ran Ollama 0.32.5 on macOS 15.3.1, Apple Silicon, 16 GiB unified memory.
`qwen3.5:2b` resolved to digest
`0689d44085e06d165161a8a9a1731344278cfb5aade63a3c3dbdb48ab54b130a`,
Q8_0, with a reported local size of 2,683,396,812 bytes. The library page also
showed a different runtime variant; the local digest, not the family name, defines
what was executed here.

The policy distinguished threats and incitement from criticism, fiction,
reporting, and condemnation. We used the native chat API, system/user separation,
a JSON output schema, temperature 0, seed 42, thinking disabled, context 4,096,
and a maximum of 256 generated tokens. See [the complete result](ollama-smoke.json)
for policy text, original cases, raw answers, counters, and timings, and
[the runner](../../../../tools/ollama_policy_smoke.py) for reproduction.

All eight responses were parseable. All eight were BLOCK. The four prohibited
cases matched their intended teaching labels; all four allowed cases failed.
For a simple disagreement, the explanation correctly said there was no threat,
but the output label was still BLOCK. The outcome demonstrates why schema validity
and a plausible explanation are insufficient acceptance criteria.

This was a single pass over eight handwritten examples, not a held-out dataset
or a policy-tuning experiment. We did not try to optimize against those same cases
and then call them an independent test. These observations do not establish the
model's general accuracy or identify the cause of the failures.

The model was unloaded and the running-model list was checked empty afterward.
Weights remain on disk for reproduction. No inference API was used; power and
hardware costs were not measured. About 12 GiB disk remained after download.
GPT-OSS Safeguard 20B was not downloaded: its approximately 14 GB listed download
would leave too little space on the machine. PolicyLM and the other specialists
were not tested locally. Their published benchmark results do not validate an
Ollama conversion.

## Pi with Luna: a useful conversation, with errors worth keeping

We installed the whole skill in a separate Pi 0.87.1 profile and used
`openai/gpt-6-luna` through OpenRouter, thinking `low`. Pi kept its normal system
prompt and default read/bash/edit/write tools. Only this skill and the opt-in
feedback extension were loaded; unrelated context files and extensions were
disabled. No expected answer, persona description, or extra research instruction
was inserted. Ordinary questions caused the model to read the skill and selected
references itself.

Four three-question conversations are preserved. They were authored and reviewed
by the development assistant; they are exploratory smoke tests, not independent
user research or a model leaderboard. Versions marked 0.4.0 were development
candidates; exact installed package hashes are in [the run inventory](conversation-runs.json).
The final evidence registry was still being assembled during those candidate tests.
Native logs and full installed snapshots remain local; only these synthetic visible
conversations were selected for publication.

| Conversation | Observation | Limit or remaining issue |
|---|---|---|
| [0.3 beginner baseline](baseline-v0.3.md) | Found the skill, gave a readable welcome, and continued into a policy draft | Attributed Shieldstral → Qwen 2B's 80.11% → 75.10% result to PolicyLM → Qwen; also described a different pair as the reverse direction |
| [0.4 beginner retest](learner-v0.4.md) | Looked up the actual requested PolicyLM → Qwen matrix cells: 80.87% for 2B and 84.87% for 4B; distinguished the new threat policy from the benchmark | A single successful retest does not prove this class of mistake is fixed; not every answer offered a next step |
| [0.4 engineering path](engineering-v0.4.md) | Explained native interfaces, the failed local smoke test, and differences among hosted APIs and GPU rental | Some citations pointed at a repository root or a transfer readout that did not support the local/HateXplain claim; new evidence links were absent from the candidate registry |
| [0.4 enterprise path](grc-v0.4.md) | Labelled enterprise governance untested, retained permissions/retrieval controls, and rejected “no training or labels” for the ensemble | The checklist was long; some source labels were imprecise. Simpler, more conversational guidance still needs user feedback |

The narrow skill correction made source-model → recipient-model attribution
explicit and directed missing pairs to the full matrix. It did not change the
underlying research results. The new local-running guidance preserves failures
and distinguishes verified provider listings from measured experience.

Across these four conversations there were 12 user questions and 29 model
responses, including tool-use steps. OpenRouter generation metadata, reconciled
after the runs, reported **$0.02030508** in total. Immediate billing lookups were
initially incomplete; missing records were not treated as free calls. This excludes
later instrumentation or release checks. It is not a projected user subscription
or production moderation cost.

The remaining evidence-link and verbosity failures are part of the findings.
The release adds the missing evidence routes; further conversations should check
whether the model actually uses the right links. We cannot infer equal behavior
from Codex, Claude Code, other Pi versions, or every inexpensive backend.

## Feedback to collect next

The author can now use the interactive lab and mark answers with `/feedback`.
An interactive terminal check confirmed skill discovery, a real Luna response,
the `/feedback` note stored as non-context metadata, `/lab-usage`, and clean exit
with a readable review. That separate check cost $0.000478985. A controlled
extension-context check also exercised the estimated-cost stop; this is not a
provider billing-limit test.
Review the latest local session for wrong claims, missing sources, excess detail,
poor next-step suggestions, and confusion between the agent backend and the
classifier being discussed. Retain examples before and after any revision.
The lab does not automatically publish or transmit user feedback to the project.
