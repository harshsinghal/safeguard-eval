# Detecting injection attempts without overblocking ordinary text

Status: implementation and dataset preparation; paid execution awaits the requested budget allocation. No new accuracy results yet. This study is separate from the older [small injection pilot](../../evals/injection/README.md), whose thresholds were tuned.

## Question

How well do three policy models and three decision models recognize a submitted prompt-injection or jailbreak attempt? Does a more explicit policy, or a few examples selected from development errors, improve their decisions? Can they do this without flagging legitimate text merely because it contains suspicious words, symbols, or non-English characters?

The six systems are **PolicyLM-1.7B, Shieldstral-1.0-3B, GPT-OSS Safeguard-20B, Kev-4B, Jev-1.14 and Clef-Flash**. All model weights remain frozen. There is no fitted score calibration, threshold search, ensemble, retrieval, or model fine-tuning.

This is a **text classification experiment**, not a test of whether a protected agent resists an attack. No supplied attack is executed, no attack URL is followed, and no model receives tools. Harmful content alone is not necessarily injection. The policy requires an attempt to override instructions, cross an instruction trust boundary, expose hidden information, or bypass an AI restriction.

## Four complementary test collections

| Collection | Test population | What it contributes |
|---|---:|---|
| [xTRam1 safe-guard-prompt-injection](https://huggingface.co/datasets/xTRam1/safe-guard-prompt-injection) | 2,060; 650 attack labels, 1,410 benign | Larger binary benchmark with a published train/test split |
| [deepset prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) | 116; 60 attack labels, 56 benign | Small, widely used binary benchmark; retain the original test split |
| [NotInject](https://huggingface.co/datasets/leolee99/NotInject) | 339 benign; 113 each in its original one/two/three-trigger subsets | Legitimate text containing attack-associated wording; a false-block stress test |
| [JailbreakBench attack artifacts](https://github.com/JailbreakBench/artifacts) | 100 GCG and 82 PAIR released prompts, both targeting Vicuna-13B | Actual attack attempts, including optimized suffixes; an attack-recall stress test |

All 18 PAIR entries with no released prompt are excluded for that reason only. Both successful and unsuccessful attempts with text are retained. The corresponding harmful goals are used in the duplicate exclusion audit, but neither model responses nor attack success flags enter a detector's input. The GCG and PAIR attempts sharing a behavior are grouped for uncertainty estimates. JBB-Behaviors alone would not supply these attack suffixes.

**Dataset limits matter.** The xTRam1 dataset is largely synthetic. Its card's narrative counts differ from the actual files; use the pinned files. Its training positives include ordinary harmful requests and task changes with no visible governing context. Deepset has similarly ambiguous task-change labels. We retain published labels and describe accuracy as agreement with those annotations, not independently verified malicious intent. Training examples must not silently redefine all harmful content as injection. Source licenses are preserved in the private downloads; xTRam1's card does not clearly declare a license, so its raw text is not republished. NotInject is MIT. Published JBB artifacts and their license are retained at a fixed commit. The deepset card contains conflicting license metadata, which is disclosed rather than resolved by assumption.

NotInject and JBB have only one class. Report benign allow rate / false-block rate for the former and attack detection rate / missed attempts for the latter. **Do not invent a balanced-accuracy score for either, or pool these unrelated collections into a headline leaderboard.** PAIR attempts may look innocuous without the original interaction; report this limitation.

## Development and test separation

1. Download immutable dataset revisions listed in `evals/prompt_injection/data.py`; hash every file.
2. Normalize text for the duplicate audit only (Unicode NFKC, casefold, whitespace). Connect exact matches and character-five-gram cosine matches at least 0.90, with a minimum length of 20 characters. Use a fixed hashing vectorizer, not a learned retrieval model. Include released JBB goals in the exclusion index. Infer on the original text.
3. Remove every training row in a connected component touching any evaluation collection. The resulting audit excludes **336 development rows: 3 deepset and 333 xTRam1**. This heuristic does not prove absence of semantic overlap or pretraining contamination.
4. Split whole remaining groups deterministically. Sample **256 fitting and 256 validation examples**: 64 per source and label in each split. Every sampled group is distinct. Unused training rows remain unused. Preserve the entire original binary tests and all eligible external stress-test rows: **2,697 final examples**.
5. Use test text only for automated duplicate checks, length checks, request construction and final inference. Do not show test examples or use test labels to author policies. The earlier deepset test was used in a prior study; this is not a new independent benchmark, although this study's configuration selection uses development data only.

## Three policy candidates, selected separately for each model

**Brief:** define the boundary and ordinary allowed cases in a short policy.

**Structured:** make the same boundary more explicit: authority impersonation, instruction overrides, secret extraction, unrestricted personas, and obfuscated instructions. Add exceptions for harmless roleplay, quoted attacks, ordinary programming and multilingual text. This is a clarification of the task, not a keyword blocklist.

**Structured plus fitting examples:** run the brief policy on the fitting split first. For each model, select two examples per label, prioritizing its mistakes, then using correctly classified fitting examples if needed. Require distinct groups and at most 280 characters per example; order by a stable hash. Attach complete, labeled quotations to the appropriate allow/block field. Freeze the chosen IDs and provenance. These labels retain the source annotation limitations; examples can hurt rather than help.

Evaluate all three on the same validation set. Select each model's policy by **mean balanced accuracy across the two source datasets**, then mean macro F1, then shorter serialized policy, then policy ID. These rules are fixed before validation. Freeze selections for **all six models before any final test inference**. The test compares the brief baseline and each selected policy; reuse a baseline result if it is also selected. Do not choose a test winner from every candidate or reselect policies for the stress tests.

This is a bounded three-candidate search, not a claim that policy optimization has reached its maximum. Fitting-derived examples are part of policy text, not nearest-neighbor retrieval. We do not introduce a synthetic obfuscation benchmark or optimize new attacks.

## Native adapters and fixed decisions

| Model | Input and decision |
|---|---|
| PolicyLM | One explicit category with violation, non-violation and exception fields. Single-line fields. Publisher **precision** preset, fixed at **0.335**; no cutoff fitting. Standard cleaner enabled; record cleaning, variants and windows. Disable only the character cap so no test message is head-truncated. BF16, one row per native batch. |
| Shieldstral | Publisher instruction/query/document wrapper; next-token yes/no probabilities; pair argmax with BLOCK on a tie. |
| GPT-OSS Safeguard | System policy and JSON-quoted content; request only an ALLOW/BLOCK JSON decision. Medium reasoning, temperature 0, 2,048 output-token ceiling. Groq via OpenRouter, provider fallback disabled. |
| Kev / Clef | Native state/question/choice interfaces and released decision heads; ALLOW/BLOCK argmax. Preserve any publisher-supplied temperature. No new temperature fitting. |
| Jev | Native OpenRouter Decisions Choice API, rather than a chat-completions imitation; require the registered resolved model and TypeSafe provider. |

Open checkpoints and provider code are pinned in `common.py` and the inherited audited native adapters. API aliases may change: record resolved identity, provider and fingerprint where exposed; do not claim an immutable hosted checkpoint. Record actual runtime environments. Run open models serially to avoid known padding/batching variation. This study does not benchmark latency or serving throughput.

For PolicyLM, its cleaner and long-message windows are part of the evaluated system, not evidence that its weights alone learned an obfuscation defense. Its model card explicitly excludes use as a sole adversarial security boundary. A benchmark score cannot override that restriction.

## Reporting and failure handling

Binary sets: accuracy, balanced accuracy, macro F1, Matthews correlation, attack recall, benign specificity, false-block and missed-attack rates, both error counts, and unresolved/coverage counts. Keep all failures in denominators; do not turn API errors or refusals into correct blocks. MCC is unavailable if predictions are unresolved. Scores are stored as evidence but not calibrated or threshold-tuned. No AUROC contest against a model that only returns categorical labels.

Show baseline-to-selected changes, paired group-bootstrap intervals, and counts alongside percentages. Report NotInject trigger-group/category slices and JBB method slices. Prespecified character-format slices (non-ASCII, Unicode formatting characters, punctuation runs, and messages over 2,000 characters) are descriptive text properties, **not validated attack-type labels**. Small slices require restraint. Do not infer that a model generalizes to unseen attack families, indirect document injection, multilingual deployment, or long enterprise conversations from this experiment.

API transport failures may be retried twice using the same request and separately recorded cost reservations. Malformed/truncated model output is unresolved, not repeatedly sampled until correct. Five native runtime failures halt execution for inspection. All changes after registration must be preserved as amendments; no silent repair or row deletion.

## Budget, execution and release

Requested ceiling: **$8**, pending user allocation from the earlier allowance or a new authorization. GPU.ai currently offers a 48 GB RTX6000 Ada at $0.65/hour; reserve at most four hours ($2.60) with provider-side automatic termination. RunPod remains the fallback if availability or credit prevents this, within the same cap. API subcaps: Jev $1, Safeguard $3.50. Combined reservations are $7.10, leaving $0.90 unallocated headroom. Verify live prices and authorization before paid work. Budget exhaustion produces an explicitly incomplete result, not a smaller test chosen after seeing results.

Publish plan, implementation, pinned manifests, policy provenance, prompt-free predictions, selections, results, costs and cleanup evidence; link from the README. Keep raw dataset text, copied labeled examples, requests, credentials, private endpoints and model weights outside Git. Provide restoration instructions for final policies whose examples are reconstructed from source IDs. Update the compute ledger and terminate all resources. Do not automatically rewrite reviewed papers, articles or released skill versions.
