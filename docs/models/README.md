# Model directory

[Research notebook](../../README.md) · [Dataset directory](../datasets/README.md) · [Results](../../README.md#current-leaderboard) · [Deployment guide](../cloud-serving/DEPLOYMENT.md)

This directory identifies the models used in our experiments, their purpose,
how we supplied instructions, and where to find their releases and our evidence.
It includes supporting encoders and retrieval models as well as classifiers.
**A model appearing here does not mean it was tested on every dataset.**

Model names link to publisher cards or the API listing used. Sizes are nominal;
an active-parameter count in a mixture-of-experts model is not its total weight
count or memory requirement. “Open weights” describes availability, not a claim
that all releases share a license or run through the same inference server.
Our experiments use text even where a publisher supports other modalities.

## Specialist policy models

These models are designed to evaluate content against supplied rules. They
accept different input structures; none should be treated as a generic chat
endpoint without checking its native interface.

| Model / publisher | Size and access used | How we used the policy | Experiments |
|---|---|---|---|
| [PolicyLM 1.7B — Musubi](https://huggingface.co/musubilabs/policylm-1.7b) | 1.7B; open weights, self-hosted | Native `Policy` / `Category` fields for violations, allowed cases and exceptions; category score becomes a decision under a specified cutoff | WildGuard, HateXplain, both injection studies and the original showcase; policy transfer, ensembles, frozen features, retrieved examples and serving. [Interface audit](../research-directions/POLICY-INTERFACE-AUDIT.md), [feature study](../contrastive-heads/README.md) |
| [Shieldstral 1.0 3B — Mistral](https://huggingface.co/mistralai/Shieldstral-1.0-3B) | 3B; open weights, self-hosted | Publisher wrapper separates policy `<Instruct>`, classification question `<Query>` and content `<Document>`; we read Yes/No scores | WildGuard, HateXplain, both injection studies and showcase; transfer, structure, ensembles, representations, corrections, retrieval and serving. [HateXplain study](../hatexplain/READOUT.md), [representation study](../shield-probe/README.md) |
| [CoPE-B-A4B — Zentropi](https://huggingface.co/zentropi-ai/cope-b-a4b) | MoE; card describes 25.2B total / 3.8B active; open weights, self-hosted | POLICY / LABELS / CONTENT classification instructions through its chat template; normalized binary label scores | WildGuard policy search and specialist ensembles; original showcase and earlier injection pilot. Not in the policy-transfer, new six-model injection or HateXplain panels. [WildGuard evidence](../../published_runs/2026-10-24-wildguard/README.md), [ensembles](../ensemble/READOUT.md) |
| [GPT-OSS Safeguard 20B — OpenAI](https://huggingface.co/openai/gpt-oss-safeguard-20b) | 20B-class MoE; open weights. Hosted API in earlier work; self-hosted vLLM in the new injection study | Policy in the system message, content in the user message, explicit JSON decision contract; reasoning/output limits are part of the configuration | WildGuard, both injection studies, original showcase and DiffusionDB demo. Not in the policy-transfer panel or continuous-score specialist ensembles. [WildGuard evidence](../../published_runs/2026-10-24-wildguard/README.md), [injection settings](../prompt-injection/RUNNING.md) |

PolicyLM's category scorer is distinct from a text-generating chat model. Its
publisher describes training from BidirLM-1.7B-Embedding, derived from
Qwen3-1.7B-Base. Our feature studies use the released PolicyLM checkpoint;
they do not separately benchmark either ancestor. Its cleaner, windowing and
cutoff also form part of the evaluated system. The publisher excludes use as a
sole adversarial security boundary; see the [model card](https://huggingface.co/musubilabs/policylm-1.7b).

For authoring guidance, start with each card, the
[OpenAI / ROOST Safeguard policy guide](https://developers.openai.com/cookbook/articles/gpt-oss-safeguard-guide)
and our [interface audit](../research-directions/POLICY-INTERFACE-AUDIT.md).
The [injection policy-change guide](../prompt-injection/POLICY-CHANGES.md)
shows concrete brief, structured and example-bearing variants. A shared authoring
source can feed several adapters; it does not guarantee identical behavior.

## Decision models / “System One”

These models take content plus a decision schema: a question and the allowed
answers. We used their native Choice interface and scores. The family label is
not evidence of a particular accuracy, latency or common architecture.

| Model / source | Size and access used | Interface and distinction | Experiments |
|---|---|---|---|
| [Jev 1.14 — TypeSafe](https://openrouter.ai/typesafe/jev-1.14) | API only in this work; parameter count and weights unavailable to the study | Native Decisions API through OpenRouter; content, policy instruction and ALLOW/BLOCK choice definitions. Recorded resolved ID: `typesafe/jev-1.14-20261014` | WildGuard, HateXplain and the new injection panel; decision-score and smart ensembles; WildGuard retrieval. [Jev readout](../jev/READOUT.md), [API protocol](../jev/PLAN.md) |
| [Kev 4B — Jared Palmer](https://huggingface.co/jaredpalmer/kev-4b) | 4B-class; released adapter/head plus open base, self-hosted | Qwen3.5-4B-Base with a LoRA adapter and pointer head over supplied options. It scores choices rather than generating a prose answer | WildGuard, HateXplain and the new injection panel; ensembles, retrieval and serving. [Decision-model study](../decision-models/README.md), [serving](../serving/README.md) |
| [Clef-Flash — Cloudflare](https://huggingface.co/Cloudflare/clef-flash) | 9B; open weights, self-hosted | Qwen3.5-9B backbone plus a joint schema decision head. We used text state and a binary Choice question | WildGuard, HateXplain and the new injection panel; decision-score and smart ensembles; serving. [Decision-model study](../decision-models/README.md), [injection study](../prompt-injection/README.md) |

The [TypeSafe model documentation](https://docs.typesafe.ai/models) describes its
hosted interface. Kev's [release code](https://github.com/jaredpalmer/kev) and
Clef's model repository describe their local implementations. Kev also needs
the matching [Qwen3.5-4B-Base checkpoint](https://huggingface.co/Qwen/Qwen3.5-4B-Base);
that dependency is not a separate generalist competitor in our tables.

We have not inspected Jev's weights or established that its internal architecture
matches either open model. API access also changes operational responsibilities:
model version, provider errors and data handling need checking. Self-hosting
instead requires maintaining the runtime and its resource lifecycle. These
studies establish no blanket latency or privacy advantage for either route.

## General-purpose language models

The Qwen comparisons ask whether ordinary instruction models can apply the same
classification intent. We supplied policy text with a system instruction,
separate user content and explicit output labels. Thinking was disabled in the
recorded moderation comparisons. All listed Qwen checkpoints have open weights.

| Exact release | Role in this repository | Evidence |
|---|---|---|
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | Frozen representations for a trained WildGuard classifier, individually and combined with PolicyLM. Not part of the five-model prompted-classification comparison | [Representation study](../activation-probe/README.md) |
| [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) | WildGuard policy search and transfer; a separate Q8_0 Ollama conversion was used in eight local teaching cases | [Generalist comparison](../qwen-policy/READOUT.md), [transfer](../policy-transfer/READOUT.md), [local check](../skill/evidence/2026-10-28/README.md) |
| [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | WildGuard and HateXplain classification; policy transfer/structure, mixed ensembles, frozen representations, training-error corrections and serving | [HateXplain](../hatexplain/READOUT.md), [representations](../shield-probe/README.md), [corrections](../policy-corrections/README.md), [vLLM/SGLang](../cloud-serving/README.md) |
| [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | WildGuard policy search; not in the cross-model transfer panel | [Generalist comparison](../qwen-policy/READOUT.md) |
| [Qwen3.5-27B](https://huggingface.co/Qwen/Qwen3.5-27B) | WildGuard policy search and transfer. Also served as the shared policy editor in the transfer study, using each source model's fitting errors | [Generalist comparison](../qwen-policy/READOUT.md), [transfer](../policy-transfer/READOUT.md) |
| [Qwen3.5-35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B) | WildGuard policy search; MoE with nominal 35B total / 3B active parameters. Not in the transfer panel | [Generalist comparison](../qwen-policy/READOUT.md) |

Qwen3.5-0.8B, Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B are different
checkpoints with different jobs. We did not use a “Qwen3.5-0.6B” model.
The local Ollama check is not a WildGuard or HateXplain benchmark and does not
validate the other models on Ollama.

## Fixed-task reference and trained classifiers

These systems classify a learned target rather than accepting a new policy
document at inference time.

| Model / source | Size and role | What we tested |
|---|---|---|
| [WildGuard — Ai2](https://huggingface.co/allenai/wildguard) | 7B; open fine-tuned moderation model | Fixed-task reference on WildGuardTest, using the official template and prompt-harmfulness field. Its response-harmfulness and refusal tasks were not scored. No custom-policy tuning arm. [Methods](../wildguard/METHODS.md), [paper](https://arxiv.org/abs/2406.18495) |
| [ModernBERT-base — Answer.AI / LightOn](https://huggingface.co/answerdotai/ModernBERT-base) | About 149M; open bidirectional encoder used for features | Frozen pooled features with separately trained linear, neural and contrastive heads on WildGuard and HateXplain. We did not fine-tune ModernBERT's backbone. [Task-classifier study](../contrastive-heads/README.md) |
| [LFM2.5-Encoder-350M — Liquid AI](https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M) | 350M; open-weight encoder under the publisher's LFM license | WildGuard: frozen-feature control versus encoder/head fine-tuning with three seeds, then serving. Separate code-file and skill-text fine-tunes use one seed per task. No HateXplain fine-tune. [WildGuard study](../liquid-finetune/README.md), [artifact study](../malicious-artifacts/README.md), [serving](../serving/README.md) |

PolicyLM and Shieldstral also supplied frozen hidden states in the
[first](../activation-probe/README.md) and [second](../shield-probe/README.md)
representation studies. A classifier trained on those states is a new evaluated
system, not the released model's native decision. Likewise, the Liquid results
belong to our trained encoder/head configuration, not its unmodified base release.

## Malicious artifact screening panel

The [code and agent-skill study](../malicious-artifacts/README.md) compares eight
systems per task: PolicyLM-1.7B, Shieldstral-1.0-3B, Qwen3.5-4B, Jev-1.14,
Kev-4B, Clef-Flash, a separately fine-tuned Liquid encoder and a character TF-IDF
logistic classifier. GPT-OSS Safeguard and CoPE were not part of this bounded
panel. This is family coverage, not a test of every model listed here.

The six frozen models each receive three prespecified policy variants through
their native interfaces; validation selects one per task. Qwen uses constrained
yes/no next-token scoring, with thinking disabled. Liquid and TF-IDF instead
learn from fitting labels and receive no policy at inference. Each task has its
own trained classifier. The Liquid run uses one seed, two learning rates and
three epochs per rate, rather than the earlier WildGuard study's three-seed
protocol. These results do not establish an architecture-only comparison.

See the [registered interfaces and selection rules](../malicious-artifacts/PLAN.md),
[model revisions](../../published_runs/2026-11-03-malicious-artifacts/registration.json)
and [runtime records](../../published_runs/2026-11-03-malicious-artifacts/runtime).
The TF-IDF baseline is a learned vocabulary plus logistic regression, not an
additional pretrained language model.

## Code embeddings with learned artifact classifiers

The [code-representation follow-up](../artifact-representations/README.md) keeps
Jina weights frozen and fits separate linear and small neural heads for source
files and skill text. It also expands Qwen 4B/9B policy search on those tasks.
These are task-trained classifiers, not policies automatically encoded by Jina.

| Checkpoint | Representation | License / evidence |
|---|---|---|
| [Jina embeddings v2 base code](https://huggingface.co/jinaai/jina-embeddings-v2-base-code) | About 161M; bidirectional encoder; mean-pooled 768-dimensional vector | Apache-2.0; [methods and pins](../artifact-representations/METHODS.md) |
| [Jina code embeddings 0.5B](https://huggingface.co/jinaai/jina-code-embeddings-0.5b) | About 494M; Qwen2.5-Coder-derived retrieval model; last-token 896-dimensional vector | CC-BY-NC-4.0; this research use is not commercial deployment permission. [Registered protocol](../artifact-representations/PLAN.md) |

## Retrieval and reranking models

These models helped choose labeled training examples to put beside a moderation
policy. They were not the final policy classifiers. All have downloadable weights.

| Model / source | Role | Evidence |
|---|---|---|
| [E5-small-v2 — intfloat](https://huggingface.co/intfloat/e5-small-v2) | Compact embedding encoder for similarity search and a nearest-neighbor voting control | [Initial retrieval study](../retrieved-examples/README.md) and [optimization](../retrieval-optimization/README.md) |
| [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 0.6B embedding model; alternative retrieval vectors | [Retrieval optimization](../retrieval-optimization/README.md) |
| [Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | 4B embedding model; larger-retriever comparison | [Retrieval optimization](../retrieval-optimization/README.md) |
| [Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | 0.6B relevance scorer to reorder retrieved candidates before selecting examples | [Retrieval optimization](../retrieval-optimization/README.md) |

BM25 was a lexical retrieval baseline, not another language model. Fitted
logistic regressions, random forests, shallow boosting models and neural heads
are described in the [ensemble](../ensemble/READOUT.md),
[smart-ensemble](../smart-ensemble/README.md) and
[task-classifier](../contrastive-heads/README.md) studies. They are learned
components with their own data and settings, not additional publisher checkpoints.

## API pilot and agent-learning checks

These entries are kept separate from completed moderation benchmarks.

The [frontier API pilot](../frontier-api/READOUT.md) sent the same 32 WildGuardTrain
prompts to each of four model routes under two reasoning settings. It tested
whether the API returned a usable classification and recorded failures and cost.
**No frontier policy search or WildGuardTest evaluation was completed.**

| Recorded API model | Access in this study | Reasoning comparison |
|---|---|---|
| [OpenAI GPT-6 Astra](https://openrouter.ai/openai/gpt-6-astra) | Hosted via OpenRouter | Low versus high; not off |
| [Anthropic Claude Opus 5.5](https://openrouter.ai/anthropic/claude-opus-5.5) | Hosted via OpenRouter | Low versus high; not off |
| [DeepSeek V4.1 Flash 1017](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017) | Hosted via OpenRouter; no local weight run | Off versus high |
| [Moonshot Kimi K3.1 Pro](https://openrouter.ai/moonshotai/kimi-k3.1-pro) | Hosted via OpenRouter; no local weight run | Off versus high |

These are historical route identities, not a claim that they remain the newest
models or that a route is available under every account. The
[pilot archive](../../published_runs/2026-10-25-frontier-pilot/README.md) records
resolved IDs, settings and the provider-routing amendment.

Separately, [GPT-6 Luna through OpenRouter](https://openrouter.ai/openai/gpt-6-luna)
was the Pi agent backend in our [skill learning tests](../skill/evidence/2026-10-28/README.md).
It answered questions about this research. That is not a test of Luna as a
moderation classifier. Codex and Claude Code are agent harnesses discussed in
the skill installation guide, not extra model rows in our moderation leaderboard.

## Find the exact version and deployment evidence

Publisher pages describe the model; our records describe the evaluated system.
Use the latter when reproducing a number.

| What to reproduce | Version and configuration record |
|---|---|
| Original specialists and adapters | [Pinned interface audit](../research-directions/POLICY-INTERFACE-AUDIT.md#pinned-documentation-checked), [WildGuard archive](../../published_runs/2026-10-24-wildguard/README.md) |
| Qwen policy comparison | [Model revisions](../qwen-policy/model-revisions.json), [registered candidates](../../evals/qwen_policy/registry.json) |
| Jev, Kev and Clef | [Jev plan](../jev/PLAN.md), [decision-model archive](../../published_runs/2026-10-29-decision-models/README.md) |
| Six-model injection comparison | [Model IDs, revisions and fixed decisions](../../evals/prompt_injection/common.py), [frozen archive](../../published_runs/2026-11-02-prompt-injection/README.md) |
| Encoders and representation classifiers | [0.8B / PolicyLM identities](../../evals/activation_probe/common.py), [ModernBERT / PolicyLM identities](../../evals/contrastive_heads/common.py), [Liquid identity](../../evals/liquid_finetune/common.py) |
| Retrieval models | [E5 revision](../../evals/retrieved_examples/common.py), [Qwen embedding/reranker revisions](../../evals/retrieval_optimization/common.py) |
| Runtime, batching, hardware and performance | [Serving study](../serving/README.md), [L4 vLLM/SGLang study](../cloud-serving/README.md), [deployment implications](../cloud-serving/DEPLOYMENT.md) |

Cutoffs, quantization, preprocessing, policy text and runtime differ across
studies. There is no single score or universal operating threshold for a model
name. Preserve the complete configuration and test both missed violations and
false blocks when changing it. Check current publisher licenses, interfaces and
provider terms for a new deployment.

Models discussed only as future candidates—for example Granite Guardian, Llama
Guard, Prompt Guard, ShieldGemma or other proposed backbones—are not completed
benchmark entries. See the [research directions](../research-directions/README.md)
and [ROOST model community](https://github.com/roostorg/model-community) for
further exploration.
