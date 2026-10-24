# Training exposure and limits on causal claims

Checked against official model documentation on 2026-10-24. These are disclosed sources, not an exhaustive contamination audit.

| Model | Disclosed training context | Implication for this study |
|---|---|---|
| [WildGuard](https://huggingface.co/allenai/wildguard) | Fine-tuned on WildGuardTrain from Mistral-7B-v0.3. | Our internal validation/audit partitions are already part of its original weight-training corpus. Only the official test is the common held-out benchmark. |
| [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b#training) | The card lists Nemotron Safety Guard v3, XGuard Train Open 200K, PolyGuardMix and synthetic data; it explicitly notes that PolyGuardMix includes WildGuardMix. | WildGuard-family training exposure is disclosed. Exact source-row/split overlap is unverified. Do not call it a model with no prior WildGuard exposure. |
| [Shieldstral](https://arxiv.org/html/2607.25857v2) | Its report describes a large mixture of public safety data plus synthetic and multimodal data, with task-specific instruction templates. The card reports WildGuardTest results. | We have not established source-row overlap or test contamination. Public-benchmark evaluation is known, but that alone is not evidence of training on the test. |
| [CoPE-B](https://huggingface.co/zentropi-ai/cope-b-a4b#training-details) | The card describes team-written policies, forum content, LLM-assisted labels and disjoint internal policy/content evaluation splits. | Internal disjointness is not a guarantee of no WildGuard overlap or no overlap in the base model's training. |
| [GPT-OSS Safeguard](https://huggingface.co/openai/gpt-oss-safeguard-20b) | A safety-reasoning adaptation of GPT-OSS with custom policy input. The card does not establish WildGuard split exclusion. | Exact WildGuard exposure is unresolved. |

All four policy models have undergone weight training. The defensible intervention here is changing written policy while holding each checkpoint and adapter fixed, with **no additional weight updates in this experiment**. A higher test score than released WildGuard would be a benchmark result, not proof that policy optimization is generally superior to fine-tuning or that the compared models have equal prior training exposure.

Sources: [WildGuard](https://huggingface.co/allenai/wildguard), [PolicyLM training and licenses](https://huggingface.co/musubilabs/policylm-1.7b#training), [Shieldstral report](https://arxiv.org/html/2607.25857v2), [CoPE-B training details](https://huggingface.co/zentropi-ai/cope-b-a4b#training-details), [GPT-OSS Safeguard](https://huggingface.co/openai/gpt-oss-safeguard-20b).
