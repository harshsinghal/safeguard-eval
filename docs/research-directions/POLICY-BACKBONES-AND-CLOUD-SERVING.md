# Choosing a policy-model backbone with cloud deployment in mind

Source review: 2 November 2026. **Survey and proposed decision process, not a new
experiment.** No training, TPU rental, or paid inference was performed for this
review. Published provider measurements below are distinct from our own GPU studies.

Gemma belongs on the shortlist. Its cloud ecosystem is a useful reason to test it,
but a generation-speed headline does not establish that a Gemma-based policy
classifier will be faster or more accurate than Liquid, Qwen, or a smaller encoder.
The decision should cover the backbone, policy interface, classification head,
serving software, and hardware together.

## What the 15,000-token headline actually measured

A close match is Rubens Zimbres's [Gemma serving study](https://medium.com/@rubenszimbres/from-1-540-to-15-338-tokens-per-second-on-a-single-tpu-chip-1c5da4e77ef2).
It reports **15,338 generated tokens/second** on one TPU v5e, with **512 concurrent
requests**, short repeated prompts, prefix caching, and **128-token outputs**.
Weights were unchanged; token selection and batching were optimized. This was an
offline generation workload, not a moderation endpoint.

The linked [methods paper, version 1.0.3](https://zenodo.org/records/21221952)
identifies the checkpoint as `google/gemma-2b` and subsequently reports 19,511
tokens/second after attention-kernel tuning. This is original Gemma, not a result
for the latest Gemma family. The author checked output consistency rather than
running a formal moderation-quality evaluation. We have not reproduced it.

Our intended service reads a policy and a submission, then returns category scores
or a short decision. Much of its work happens while reading the input. An encoder
with a classification head need not generate tokens at all. Neither dividing the
headline by our input length nor treating it as decisions/second would give a
valid capacity estimate.

A [Google Cloud classification study](https://cloud.google.com/blog/topics/developers-practitioners/not-all-llm-workloads-are-equal-benchmarking-tpu-performance-on-classification-vs-generation)
is closer to our use case: approximately 4,000 input tokens and 10 output tokens,
using Gemma 3 12B and 27B on a four-chip TPU v6e configuration. It shows different
scaling patterns for classification and generation. Its normalized results and
warnings about unstable high-concurrency measurements do not establish an absolute
latency or cost advantage for our smaller classifiers.

## Gemma does not have exclusive access to TPU improvements

[Google's current inference guide](https://docs.cloud.google.com/tpu/docs/tpu-inference)
documents vLLM and SGLang on TPU with both JAX and PyTorch backends. The
[October TorchTPU announcement](https://developers.googleblog.com/announcing-new-vllm-and-sglang-inference-engines-on-tpu/)
extends the native PyTorch serving path.

The [vLLM TorchTPU support table](https://vllm-torchtpu.readthedocs.io/en/latest/user_guide/supported_models/)
covers several model families, including Qwen, Llama, and Gemma, with different
levels of validation. It documents pooling support, but does not establish tested
support for our exact PolicyLM, BidirLM, or Liquid rule-matching implementations.
Absence from that table is an unverified combination, not proof of incompatibility.

There are three separate questions:

1. Can the framework execute the model correctly?
2. Does the serving engine support its attention, head, and output contract?
3. Does that combination run efficiently under our traffic?

Changing a causal Gemma model into a bidirectional encoder changes how tokens
interact. Adding a custom category-scoring head changes the output path. Those
changes may require additional serving work even when the original Gemma decoder
already has optimized kernels. The same qualification applies to a Qwen-derived
PolicyLM and Liquid's encoder. An ordinary PyTorch service can also be appropriate;
vLLM is not a requirement for every classifier.

## Backbones worth considering

The size figures describe different architectures and are not performance rankings.
The deployment assessments are engineering judgments to test, not measured TPU results.

| Candidate | Why it belongs in the survey | What we would need to establish |
|---|---|---|
| [ModernBERT, 149M / 395M](https://huggingface.co/answerdotai/ModernBERT-base) | A compact encoder designed for downstream tasks, with 8,192-token context and standard Transformers integration. Useful as an efficiency control. | Whether policy-conditioned training teaches it to follow unfamiliar rules and exceptions. Its published GPU optimizations do not prove TPU performance. |
| [mmBERT, 140M / 307M](https://huggingface.co/jhu-clsp/mmBERT-base) | A multilingual ModernBERT-family option when the enterprise needs more than English. | Quality on the actual languages, code switching, and policy translations. Language coverage in pretraining is not a moderation-quality guarantee. |
| [BidirLM based on Gemma 3, 270M / 1B](https://huggingface.co/BidirLM/BidirLM-1B-Embedding) | Already adapted into a bidirectional encoder; the 1B variant is a plausible starting point for a PolicyLM-like design. | A policy-aware classification head, policy-conditioned training, and correct, efficient deployment of its custom encoder implementation. |
| [EmbeddingGemma 2](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2) | A current Google representation model with a 270M text component; the complete multimodal model is 740M. Text-only loading is relevant here. | Whether adapting its representations to joint policy/content judgments works. Retrieval and embedding benchmarks are not evidence of policy interpretation. |
| [Gemma 3 1B](https://huggingface.co/google/gemma-3-1b-pt) or [Gemma 4 E2B](https://ai.google.dev/gemma/docs/core/model_card_4) | Keep the causal architecture and use a final-position classification head or a short label output. This preserves more of the ordinary decoder-serving path. | Head/output support, policy-following quality, and actual loaded memory. E2B means 2.3B effective parameters but 5.1B including embeddings; it is not equivalent in footprint to a 2B dense encoder. |
| [Qwen3 0.6B](https://huggingface.co/Qwen/Qwen3-0.6B-Base) and [Qwen-derived BidirLM 1.7B](https://huggingface.co/BidirLM/BidirLM-1.7B-Embedding) | A small conventional decoder option and the encoder lineage used by PolicyLM. These help separate a new training recipe from a change of model family. | Exact small-checkpoint and head support. TPU support for Qwen decoders does not automatically cover their bidirectional derivatives. |
| [Liquid LFM2.5 encoders, 230M / 350M](https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M) | Compact bidirectional models; we already have experience fine-tuning the 350M encoder. | Efficient TPU execution of its hybrid convolution/attention blocks and custom head. A GPU or CPU may be the more practical target if that integration work is substantial. |

There are also existing policy models to use before training replacements.
[PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b) is our principal
policy-conditioned reference. Liquid publishes a
[350M Policy Linter](https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M-Policy-Linter)
that scores text tokens against free-text rules. We have not evaluated that model;
its token scores would need a documented, validation-selected conversion into our
prompt-level decision. [ShieldGemma 2B](https://huggingface.co/google/shieldgemma-2b)
provides an existing Gemma-family safety reference, although its four documented
harm categories do not establish broad enterprise-policy coverage.

License and redistribution terms belong in checkpoint selection. ModernBERT and
Gemma 4 advertise Apache 2.0; Gemma 3 uses Gemma terms and Liquid lists the LFM
Open License. A derivative's metadata should not be treated as resolving all
upstream obligations. Pin and review the actual artifacts before distribution.

## What our own experiments contribute

Our [L40S serving study](../serving/README.md) measured **358.4 decisions/second**
for the fine-tuned Liquid encoder at 32 requests in flight, with a **103.1 ms p95**.
The same study found a **6.6-fold** Shieldstral throughput improvement when enabling
shared-policy prefix caching. These are measurements for specific workloads and
runtime configurations, not cross-cloud guarantees.

The Liquid classifier used no policy document at inference. It learned a fixed
harmfulness boundary. Its speed does not establish the speed or quality of Liquid's
Policy Linter, or of a policy interpreter we might train.

Our [L4 study](../cloud-serving/README.md) found that input length and concurrency
affected Qwen waiting time much more than the small gap between vLLM and SGLang.
That is directly relevant to enterprise policies: the document, examples, and
submitted text all add work. The best engine name alone does not settle deployment.

## The architecture decision that matters for repeated policies

A causal model can sometimes reuse computation for an unchanged policy at the
start of the input. Its earlier token states do not depend on the later submission.
Cache boundaries, engine support, and tenant traffic still determine actual savings.

In a fully bidirectional joint encoder, policy-token states depend on the submitted
content as well. Reusing those states across different submissions is generally
not equivalent computation. Separately encoding the policy would enable different
caching opportunities, but changes the model design and must be tested for lost
rule/content interactions. This is an architectural deduction, not a measured TPU
result.

For a single decision, speculative decoding has little work to accelerate. For a
non-generating encoder there is no decoding stage. More useful priorities are
efficient input processing, short batching delays, sensible length buckets, and
the smallest model that meets the quality requirements.

## Recommendation: compare a few systems before choosing the backbone

**For a compact PolicyLM-like research model, prioritize Gemma-based BidirLM 1B
and a conventional encoder control. Keep Liquid in the comparison, initially
through its existing Policy Linter.** Retain released PolicyLM as the quality
reference. This is a candidate order, not a claim that Gemma will win.

If the decisive requirement is the least custom work on a standard TPU generation
server, first check a causal Gemma with short label output and a small Qwen control.
That is a different implementation choice from building a bidirectional model.
Test a custom head only after its intended runtime path is clear. A newer or larger
Gemma should enter if the compact candidates cannot meet the quality target, not
solely because it is newer.

The proposed sequence is deliberately bounded:

1. **Define the decision contract.** Supply policy text plus content and return
   category scores. Fix input limits, expected category counts, languages, false-block
   and missed-violation tolerances, and an end-to-end waiting-time target. A 200 ms
   p95 target could be a planning example; it is not a measured capability or an
   agreed requirement.
2. **Check serving feasibility before substantial training.** Verify the exact
   attention mask and head on GPU and one suitable TPU configuration. Compare
   scores with a trusted reference implementation, including long inputs, padding,
   and multiple categories. Stop a path that requires disproportionate kernel work.
3. **Run a small matched quality pilot.** Use the same policy/content/label triples,
   training budget, and development splits for the shortlisted trainable models.
   Hold out policy families as well as examples. Include identical content under
   policies that correctly require different decisions, exceptions, and equivalent
   policy paraphrases. WildGuard and HateXplain remain useful fixed-task checks;
   alone they cannot establish an adaptable enterprise policy interpreter.
4. **Measure the finalists as services.** Compare an L4 GPU with an available
   single-chip TPU v6e configuration, or a documented alternative if the selected
   runtime requires it. Include a CPU baseline for the compact encoder. Use the
   same text, record each tokenizer's lengths, and separately run length-controlled
   profiles. Cover short through long inputs, one versus several policy categories,
   steady traffic and bursts, shared and changing policy prefixes.
5. **Select at matched quality and waiting time.** Report balanced accuracy, false
   blocks, missed violations, valid decisions/second within the latency target,
   p50/p95/p99, failures, and cost per million decisions at realistic utilization.
   Include warm capacity, startup, host resources, and replicas. Recheck quality
   after quantization or runtime changes; speed alone is insufficient.

The [vLLM TorchTPU repository](https://github.com/vllm-project/vllm-torchtpu)
currently recommends v7x for its continuously tested path, lists v6e as supported
without CI coverage, and calls v5e/v5p experimental. This is that backend's status,
not a judgment on all TPU software. Exact engine versions, chip count, quota,
regional capacity, and cold-start behavior must be part of any registered run.
The old v5e headline and a new PyTorch TPU stack are not the same deployment.

Training on a GPU need not prevent later TPU inference. What must carry across is
a compatible implementation of the trained graph, with checked numerical behavior.
We should therefore select for policy quality and maintainable serving together,
rather than assume that the hardware used during fine-tuning determines deployment.

This survey does not choose a final checkpoint or authorize the proposed runs.
The next deliverable, if pursued, is a short compatibility report and registered
pilot—not simultaneous full training campaigns for every model in the table.
