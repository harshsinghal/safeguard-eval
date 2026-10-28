# Model downloads and policy-authoring guidance

These are primary-source reading routes checked on 28 October 2026, not a
leaderboard or an endorsement. The machine-readable
[external catalog](external-sources.json) records each source's role. Its links
are live and may change; our experiment identities and results are separately
pinned in [sources.json](sources.json). Consult [models.md](models.md) for what our
adapters actually did.

## Start with the checkpoint we tested

| Family | Official checkpoint / download page | Recorded project role |
|---|---|---|
| Musubi PolicyLM | [musubilabs/policylm-1.7b](https://huggingface.co/musubilabs/policylm-1.7b) | Custom policy specialist |
| Mistral Shieldstral | [mistralai/Shieldstral-1.0-3B](https://huggingface.co/mistralai/Shieldstral-1.0-3B) | Custom policy specialist; our tests used text |
| Zentropi CoPE | [zentropi-ai/cope-b-a4b](https://huggingface.co/zentropi-ai/cope-b-a4b) | Custom policy specialist |
| OpenAI GPT-OSS Safeguard | [openai/gpt-oss-safeguard-20b](https://huggingface.co/openai/gpt-oss-safeguard-20b) | Custom policy specialist; 20B was tested |
| Ai2 WildGuard | [allenai/wildguard](https://huggingface.co/allenai/wildguard) | Released fixed-task baseline, prompt-harmfulness output |
| Qwen3.5 | [2B](https://huggingface.co/Qwen/Qwen3.5-2B), [4B](https://huggingface.co/Qwen/Qwen3.5-4B), [9B](https://huggingface.co/Qwen/Qwen3.5-9B), [27B](https://huggingface.co/Qwen/Qwen3.5-27B), [35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B) | General-purpose comparators; thinking disabled |

These pages host cards and weight files. Reading a card does not require loading
weights. For reproduction, get the exact revision from the frozen run, not the
latest checkpoint with a similar family name. A newer card may describe a newer
interface. Check access terms, supported runtime, tokenizer, and chat template
before integration; this skill does not promise a hosted endpoint or serving cost.

## OpenAI and ROOST: the policy is a specification

The [GPT-OSS Safeguard introduction](https://openai.com/index/introducing-gpt-oss-safeguard/)
explains why custom policies are supplied at inference time. The
[OpenAI/ROOST policy guide](https://developers.openai.com/cookbook/articles/gpt-oss-safeguard-guide)
is the practical starting point: define the decision and categories, state
exceptions and priority, use boundary examples, and specify output labels.
It places policy in the system role and content in the user role. Safeguard expects
Harmony formatting; use the appropriate tokenizer/runtime support rather than
inventing a generic text wrapper.

The guide's length and example-count suggestions are provider recommendations,
not optima established by our experiments. Test them against the chosen checkpoint
and task. A rationale is a model output, not proof of how its weights reached the
decision. The [teen safety policy pack](https://github.com/openai/teen-safety-policy-pack)
offers sample policies and associated evaluation material. Adapt its scope and
check its usage terms; we did not evaluate that pack in this project.

## Musubi: keep native categories explicit

The [PolicyLM card's policy-writing section](https://huggingface.co/musubilabs/policylm-1.7b#writing-a-policy)
recommends concise rules separated by violation type. Its native fields distinguish
violations, non-violations, and exceptions. Do not flatten these into an arbitrary
system prompt and call it equivalent. Built-in category modes and custom-policy
mode are different interfaces.

Our early WildGuard policy grouped harms into one broad category. The study did
not exhaustively optimize category decomposition. This is an important limitation
when interpreting its results, rather than evidence that native category design
does not matter. Provider benchmark tables remain separate from our comparisons;
their score alone does not reveal every competitor's rendered prompt.

## Mistral: separate the instruction, question, and content

Read the [Shieldstral card](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[release article](https://mistral.ai/news/shieldstral/), and
[paper](https://arxiv.org/abs/2607.25857). The documented interface separates policy
context in `Instruct`, a binary question in `Query`, and content in `Document`,
under a fixed system instruction. Our adapter scored Yes/No for the BLOCK question.
Changing the question's orientation without changing the score mapping reverses
the meaning of the output.

The publisher discusses broader capabilities, including images. Our text studies
do not validate those capabilities or their multilingual performance. A provider
description of scores does not remove the need to choose a decision cutoff on
your own development data.

## Zentropi: policy changes and version changes both need tests

The [CoPE-B-A4B card](https://huggingface.co/zentropi-ai/cope-b-a4b) supplies its
current prompt and runtime contract. Its migration notes specifically call for
checking the changed template, thresholds, and policy optimization when moving
between model generations. Our CoPE-B adapter supplied policy, labels, and content
through that checkpoint's chat template.

The [CoPE paper](https://arxiv.org/abs/2512.18027) explains the earlier model's
training approach; it is not an exact architecture specification for CoPE-B.
Zentropi's [policy-steerability article](https://blog.zentropi.ai/introducing-the-policy-steerability-benchmark/)
is useful for thinking about cases whose correct answer changes with the policy.
Its benchmark was not publicly downloadable when checked. Treat its reported
results as provider claims, not independently reproduced results or a ready-made
public train/test dataset for this project.

## Ai2 and Qwen: keep their roles clear

The [WildGuard paper](https://arxiv.org/abs/2406.18495) covers the upstream moderation
tasks and dataset. Our baseline uses its fixed task template; we did not optimize
arbitrary policy text for WildGuard. Qwen3.5 is a general-purpose comparator, not
Qwen Guard. Its own model card documents generation settings; our recorded tests
turned thinking off. Do not silently substitute a thinking-enabled or newer model
and reuse the historical score.

## Broader discovery, explicitly outside our evaluated panel

The [ROOST Model Community](https://github.com/roostorg/model-community) provides
model-specific resources, an [open safety model guide](https://github.com/roostorg/model-community/blob/main/resources/RMC%20Guide%20to%20Using%20Open%20Safety%20Models.md),
and policy-pack pointers. [Awesome Safety Tools](https://github.com/roostorg/awesome-safety-tools)
is a wider directory. Use these to find the publisher, then inspect its current
card and implementation. Directory membership does not imply equivalent tasks,
arbitrary-policy support, or an independent performance ranking.

| Starting point | Why consult it | Boundary for this skill |
|---|---|---|
| [IBM Granite Guardian](https://github.com/ibm-granite/granite-guardian) | Risk definitions, custom criteria, and RAG-related checks | Not evaluated here; custom criteria still require tests |
| [Llama Guard 4](https://huggingface.co/meta-llama/Llama-Guard-4-12B) | Safety taxonomy and text/image classification | Not evaluated here; inspect taxonomy and template before proposing a new rule |
| [Llama Prompt Guard 2](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M) | Detection of attempts to override instructions | Not evaluated here; attack detection is distinct from general harmfulness |
| [ShieldGemma](https://huggingface.co/google/shieldgemma-9b) | Safety guideline formats for prompt-only and prompt/response classification | Not evaluated here; different family from Shieldstral |
| [ROOST's Roblox resources](https://github.com/roostorg/model-community) | Links to PII, Sentinel, and voice-safety resources | None evaluated here; specialized tools need task-specific assessment |

For an unfamiliar name, resolve the publisher and exact checkpoint before
describing its interface. Do not guess a Hugging Face ID or treat every safety
model as a drop-in policy interpreter. Use [search.md](search.md) when this guide
does not answer the user's question.
