# What we actually served

| System | Backend in this study | Preserved behavior |
|---|---|---|
| Shieldstral 1.0 3B | vLLM 0.32.0, text only | Publisher-style system instruction and Instruct/Query/Document sections; one generated token and both label scores |
| Qwen3.5 4B | vLLM 0.32.0, text only | Existing system policy and separate user input; thinking off; free A/B output, maximum eight tokens |
| WildGuard 7B | vLLM 0.32.0 | Official fixed-task completion template, slow tokenizer, one BOS; parse all three fields, use prompt harmfulness |
| PolicyLM 1.7B | Publisher helper + PyTorch HTTP batch server | Bidirectional category-slot scoring, rule/exception fields, native cleaning and window handling |
| Kev 4B | Publisher decision head + PyTorch HTTP batch server | Pinned merged adapter on Qwen3.5-4B-Base, native typed choice schema and head |
| Clef-Flash 9B | Publisher decision head + PyTorch HTTP batch server | Pinned joint-schema serialization and native head |
| Fine-tuned Liquid encoder 350M | Transformers + PyTorch HTTP batch server | Selected encoder weights, bidirectional convolutions/attention, masked mean pooling and learned linear head; no policy text |

Model identifiers, exact revisions, policies and cutoffs are in
[the registration](REGISTRATION.json). These are seven deployable *systems*, with
different input lengths and output contracts. They are not equal-quality or
architecture-matched configurations.

vLLM's [supported-model documentation](https://docs.vllm.ai/en/latest/models/supported_models/)
and [structured-decision documentation](https://docs.vllm.ai/en/latest/models/structured_decisions_models/)
are evolving. In particular, the main branch inspected during preparation had
Clef-Flash and bidirectional LFM2 support absent from the pinned stable release's
registry. Even an encoder backend would still need to load our exact trained
classification head and reproduce its pooling. A generic causal LFM2 or a
converted last-token classifier would be a different system.

Native backends here use a small queue that groups up to 8 or 32 arriving
requests after a 2 ms admission window. They are useful self-hosting baselines;
they are not measurements of those models running inside vLLM. Compiler settings,
fused native kernels, different hardware and dedicated serving implementations
could improve them. This pilot does not determine any model's performance ceiling.

Publisher interfaces: [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b),
[Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[Qwen](https://huggingface.co/Qwen/Qwen3.5-4B),
[WildGuard](https://huggingface.co/allenai/wildguard),
[Kev](https://huggingface.co/jaredpalmer/kev-4b),
[Clef-Flash](https://huggingface.co/Cloudflare/clef-flash), and
[Liquid encoder](https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M).
