# Nearby-size general-purpose classification

This follow-up uses Qwen3.5's post-trained checkpoints to classify the same WildGuard prompts as the specialized policy models. See the [protocol](../../docs/qwen-policy/PLAN.md), [notebook](../../docs/qwen-policy/NOTES.md) and [progress](../../docs/qwen-policy/progress.json). Results are pending.

The original WildGuard experiment remains immutable. This package adds a general-purpose system-prompt adapter, five-candidate validation selection, explicit final-inference freeze, and matched historical comparisons. It reuses the existing metrics and prompt-free export/reproduction tools.

The system prompt renders the purpose, block, allow and precedence fields. Its fixed output wrapper maps ALLOW to A and BLOCK to B. It excludes policy IDs and source labels. The user message contains only the JSON-encoded request. Non-thinking mode is explicit; primary decisions use the complete free-generated answer. Invalid output and refusals are errors, even if token probabilities could suggest a label. Scores support a separate validation-selected threshold control only when coverage permits.

Run against a localhost vLLM endpoint:

```sh
python3 -m evals.qwen_policy.run \
  --model Qwen/Qwen3.5-2B --revision 15852e8c16360a2fea060d615a32b45270f8a8fc \
  --policy evals/wildguard/policies/p0.json \
  --data /private/data/fit-search.jsonl --stage search \
  --out /private/runs/qwen-2b-search-p0
```

Use a new output directory. Test/audit runs additionally require a freeze, including source, policy, revision, setting and population hashes. Private raw traces contain gated prompts; do not publish them. The registry binds every candidate to complete fitting and validation runs on matched populations.

```sh
python3 -m evals.qwen_policy.study select --registry evals/qwen_policy/registry.json \
  --runs /private/runs --out /private/selection.json
python3 -m evals.qwen_policy.study freeze --registry evals/qwen_policy/registry.json \
  --selection /private/selection.json --runs /private/runs --out /private/freeze.json
```

Final analysis requires all frozen configurations on all labeled official-test rows and the registered internal-audit sample. It compares p0, shared p2 and independently selected policies with the corresponding historical policy-model runs. Qwen3.5-9B is compared with the fixed WildGuard baseline. The official test was already seen in the prior study, so the follow-up remains exploratory even though new prompts are frozen before new Qwen test inference.
