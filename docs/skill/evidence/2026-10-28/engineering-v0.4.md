# Safeguard Eval — Pi conversation review

Run: 20261028T194334Z-3c5d0f. Model: openai/gpt-6-luna. Skill: 0.4.0.

Local review only. Check for private information before sharing. No automatic upload.
Original visible turns are in append order; IDs preserve branches. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 21,
    "output": 2235,
    "cacheRead": 142318,
    "cacheWrite": 37624,
    "totalTokens": 182198
  },
  "model_responses": 7,
  "pi_estimated_cost_usd": 0.00724578,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.0072457799999999985,
  "billing_records_available": 7,
  "billing_records_requested": 7
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 2c02bdc4 (parent feb804b0)

Can I use the same policy text with PolicyLM and Qwen? What did your experiments actually find?

## Assistant · 30d4c4bb (parent 971de726)

**Yes—you can reuse the policy’s meaning, but don’t assume the same text will work equally well unchanged.** Keep a common source for the rules, exceptions, and examples, then render it through each model’s supported input format and test both. PolicyLM takes structured fields such as violation rules, allowed cases, and exceptions; Qwen used a system instruction plus policy text and explicit output labels. So even our experiments didn’t send identical raw prompts to both. [Model interfaces](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/evals/run.py)

**What the transfer experiment found:** on the WildGuard prompt-harmfulness task, a Shieldstral-selected policy gave PolicyLM **74.57% accuracy**, versus **85.05%** with PolicyLM’s initial policy. The Qwen-2B-selected policy gave PolicyLM **81.75%**. But those are specific policies and configurations—not proof that every policy transferred from Qwen to PolicyLM will hurt. [Transfer results](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/published_runs/2026-10-25-policy-transfer/README.md) · [Full transfer matrix](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/published_runs/2026-10-25-policy-transfer/analysis.json)

That same study also showed transfer could help: a Qwen-2B-selected policy raised Shieldstral from **87.82% to 90.76%**. And on a separate HateXplain task, removing all examples changed accuracy in opposite directions for Shieldstral (**52.4% → 61.0%**) and Qwen (**72.5% → 61.8%**). These are fixed benchmark settings, not universal rules about examples or model quality. [Studies and findings](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/policy-transfer/READOUT.md)

**Practical takeaway:** share the policy’s intent, adapt its packaging where needed, and evaluate each model on the errors that matter to you—especially missed violations and false blocks. The experiments support testing the policy, model, adapter, and decision setting together; they don’t establish that one text is universally optimal.

## User · 2e39454e (parent 30d4c4bb)

Can I run these policy models locally with Ollama? What have you actually tried, and how would I start?

## Assistant · 322494cb (parent 5da53469)

**Yes, for some checkpoints—but Ollama support is model-specific.** What we’ve actually tried is **Qwen3.5:2b**, not PolicyLM or the other specialists.

On **Ollama 0.32.5**, running Qwen3.5:2b in Q8_0 on an Apple Silicon Mac with 16 GiB unified memory, our smoke test returned parseable JSON for all eight handwritten cases. But it got only **4 of 8 labels right**: it blocked all eight, including the four intended allow cases. That’s evidence the local integration ran—not a useful accuracy estimate or a rerun of our benchmark experiments. We have **not tested PolicyLM on Ollama** on that machine.

To try the same basic setup, first check available disk and memory, then:

```bash
ollama pull qwen3.5:2b
python3 tools/ollama_policy_smoke.py --output work/my-local-smoke.json
```

The second command is the project’s recorded smoke-test runner and requires an existing checkout; it does not download the model. It records the model digest, settings, responses, timings, token counts, and unload status. For a different setup, follow the checkpoint’s own template and interface, and check label orientation, context length, and output parsing. An unofficial Ollama conversion of PolicyLM should **not** be assumed to preserve PolicyLM’s native scoring interface.

For Safeguard Eval’s recorded local test details, see [the running-model guide](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/). It also describes an Ollama GPT-OSS Safeguard option, but we did not run that on the test Mac. In particular, a successful download or valid JSON is only an integration check; evaluate allowed and blocked cases on your own test set before relying on the results.

## User · c8e68fa4 (parent 322494cb)

If local hardware is too small, should I use Groq, Cerebras, GPU.ai or Runpod? Do they all offer Safeguard?

## Assistant · 23dabac3 (parent c8e68fa4)

**No—don’t assume all four offer GPT-OSS Safeguard.** In the project’s provider check, dated **28 October 2026**, the options differed:

| Option | What the project found | What that means |
|---|---|---|
| **Groq** | Documented `openai/gpt-oss-safeguard-20b`, listed as a **preview** model | The clearest hosted Safeguard route in that check. Verify it’s still available to your account and review current pricing, limits, and data terms. |
| **Cerebras** | Its shared catalog listed ordinary GPT-OSS 120B and Qwen 3.8 27B, but **did not establish a shared GPT-OSS Safeguard endpoint** | Don’t treat ordinary GPT-OSS or a similarly named model as Safeguard. |
| **GPU.ai** | Used for completed historical GPU experiments | This is a rented-GPU route, not evidence of a hosted Safeguard API or a quality advantage. |
| **Runpod** | Recorded as a possible fallback; no completed Runpod benchmark run | Also a rented-GPU route. You’d need to set up the model/runtime yourself and verify the exact checkpoint works. |

**How I’d choose:** try Groq if you want a managed Safeguard endpoint and it’s currently available under terms you’re comfortable with. Choose a rented GPU if you need more control over the runtime or model files; compare total costs, including setup, downloads, idle time, and storage, and make sure to verify the instance is terminated afterward. If a provider offers a different model, that doesn’t make it Safeguard or reproduce our Safeguard results.

These are the project’s recorded provider findings, **not a live availability check**. See the [running-model guide](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/) and its links to [Groq’s Safeguard listing](https://console.groq.com/docs/model/openai/gpt-oss-safeguard-20b) and [Cerebras’ model catalog](https://inference-docs.cerebras.ai/models/overview); check current provider documentation before signing up or sending data.

