# Methods: general-purpose Qwen comparison

This is a follow-up to the completed WildGuard policy-tuning study. It compares deployed classification systems on identical examples, rather than isolating a causal effect of specialized training. The protocol was published before new Qwen inference; candidate prompts were published before their evaluation; final choices are frozen before new audit/test inference. Previous WildGuardTest results were already known to the experimenter.

## What changes and what stays fixed

The new systems use official post-trained Qwen3.5 checkpoints. Their weights remain fixed. The policy's purpose, block, allow and precedence fields become a system instruction; the submitted request is JSON-encoded in the user message. The fixed wrapper says to classify rather than answer, maps ALLOW to A and BLOCK to B, and requires exactly one letter. The wrapper is identical across Qwen models and candidates. Source responses, gold labels, categories and adversarial flags are excluded from requests.

The original specialist predictions are reused, with their own pinned model versions and native interfaces. Their original policies, thresholds, code and evidence are preserved. A policy document and a system prompt both communicate instructions; the central comparison is which model interprets those instructions, with interface and deployment differences disclosed.

## Models

| Specialist | Qwen comparison | Match and limits |
|---|---|---|
| PolicyLM-1.7B | Qwen3.5-2B | Nearby dense language-model size; Qwen is larger |
| Shieldstral-1.0-3B | Qwen3.5-4B | Nearby dense language-model size; Qwen is larger |
| WildGuard 7B | Qwen3.5-9B | Nearby dense language-model size; Qwen is larger |
| CoPE-B-A4B: 25.2B total / 3.8B active | Qwen3.5-27B; Qwen3.5-35B-A3B | Separate approximate total-parameter and active-parameter matches |
| Safeguard-20B: about 20.9B total / 3.6B active | Qwen3.5-27B; Qwen3.5-35B-A3B | Separate approximate total-parameter and active-parameter matches |

Five unique Qwen deployments serve seven registered pairings. The two larger models are reused, not separately rerun for each specialist. Qwen names describe language-model sizes. Full checkpoint parameter counts, including vision-related weights, are 2.274B, 4.660B, 9.653B, 27.781B and 35.952B, recorded with revisions in [model-revisions.json](model-revisions.json). Only text inputs are evaluated. Similar active parameter counts do not imply equal memory, latency or compute; model age, training data and architecture are uncontrolled.

Official model sources: [2B](https://huggingface.co/Qwen/Qwen3.5-2B), [4B](https://huggingface.co/Qwen/Qwen3.5-4B), [9B](https://huggingface.co/Qwen/Qwen3.5-9B), [27B](https://huggingface.co/Qwen/Qwen3.5-27B), [35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B), and [CoPE](https://huggingface.co/zentropi-ai/cope-b-a4b). Qwen's original exposure to WildGuard data is unverified.

## Data and search

The dataset is [AllenAI WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix), pinned to `d29c47f41c8b51348b5c8e8c81c039b3132b66d1`. Its upstream access conditions and ODC-BY attribution apply. The experiment reuses the prior study's grouped partitions and exact file hashes: 1,024 fitting examples, 512 validation examples, 512 internal-audit examples, and every one of the 1,699 official-test rows with a non-null prompt-harmfulness label. Twenty-six null-label test rows are excluded, as in the prior study. Pilots use 256 fitting rows. No expanded 8,192-row fitting phase is added in this budgeted follow-up.

The target is **prompt harmfulness**, a binary classification. ALLOW corresponds to unharmful and BLOCK to harmful. It does not score assistant-response harmfulness or refusal, actual image content, religious iconography, or downstream attack success. No REVIEW label is used. WildGuardTrain labels are model-generated; WildGuardTest labels are human annotations. Train and test cover the same broad taxonomy; categories were not held out. Test has 945 ALLOW and 754 BLOCK rows, including 903 vanilla and 796 adversarial prompts. The prior lexical overlap audit found two test rows related to the full training population, but neither matched this exact fitting/validation search sample. See the unchanged [optimizer overlap audit](../../published_runs/2026-10-24-wildguard/optimizer-overlap.json). This does not establish absence of semantic overlap or model-training exposure.

Each Qwen model evaluates the unchanged initial taxonomy (p0), concrete-harm prose (p1), and shared boundary checklist (p2). Two additional drafts per model are written from fitting errors. No copied source examples, demonstrations, names or entity-specific exceptions are inserted. Aggregate validation scores are visible, but validation prompts and individual mistakes are not inspected for editing. All five candidates per model are retained, including failed revisions. This is 25 model/candidate combinations and 13 distinct policy texts.

Selection maximizes validation accuracy, with ties resolved by shorter policy text and then lexicographic ID. Final comparisons use p0, shared p2 and the selected policy; identical configurations are evaluated once and assigned multiple roles. Five candidates matches the earlier candidate count, but inherited shared policies, prior benchmark knowledge and adaptive human/assistant effort prevent a claim of equal search effort. Policy edits include explicit scope hypotheses, such as harmful endorsements and sensitive health information, as well as wording and benign-case exceptions.

## Inference and scoring

One GPU.ai 96 GB RTX PRO 6000 Blackwell Server runs all new models sequentially. vLLM 0.31.0 serves pinned BF16 checkpoints in eager mode with 32 concurrent requests, a 32,768-token maximum context, temperature 0, top-p 1, and eight maximum output tokens. Qwen thinking is explicitly disabled using `enable_thinking=false`. This fixed greedy deployment differs from the model cards' recommended sampling defaults. Reasoning-enabled variants are outside this study.

Primary predictions use the complete free-generated answer with a successful stop. Only A or B, allowing surrounding whitespace, is accepted. Refusals, explanations, truncations and transport errors are counted as incorrect, with no retries or hidden label repair. No constrained decoder forces valid labels. Historical Safeguard used medium reasoning and native MXFP4, while Qwen uses non-thinking BF16; other specialists use their recorded native classification adapters. These are material deployment differences.

A separate control selects a label-score threshold on validation over 0.01–0.99; ties favor the value closest to 0.5, then the lower value. All invalid outputs remain errors. The score normalizes the maximum reported token probability for each stripped A/B label variant. It is not a calibrated harmfulness probability. A control is unavailable if valid-answer score coverage is incomplete. An additional paired contrast between selected free labels and the calibrated initial prompt was added during final inference, after some test scores were visible; it is secondary and changes no selection or primary outcome. Historical threshold controls are reused from the earlier freeze; WildGuard and Safeguard retain their explicit-label deployments where no score control exists.

Accuracy is primary. Harmful-class F1, macro F1, harmful recall, benign false-block rate, error counts, adversarial/vanilla slices and category slices are also retained. Accuracy counts every output failure as wrong. The failure-aware harmful F1 and the separately reported official failure-to-wrong-label convention can differ for specialist runs with errors. All new-versus-old comparisons match IDs, source prompt hashes, gold labels and prompt groups.

Paired accuracy intervals sample connected prompt groups with replacement, using 2,000 replicates and seed 20261024. They are exploratory, unadjusted for multiple comparisons, conditional on the chosen prompts, and exclude annotation uncertainty and runtime variation. The pilot-versus-search overlap supplies a descriptive repeated-input diagnostic under different batch contexts; it is not a controlled repeatability experiment. Historical and new runtime measurements do not support a clean speed ranking.

## Documentation and evidence

The [plan](PLAN.md), [notebook](NOTES.md), [candidate registry](../../evals/qwen_policy/registry.json), [writing map](WRITING.md) and [public evidence directory](../../published_runs/2026-10-25-qwen/) preserve hypotheses, unsuccessful edits, selection, predictions, source/runtime versions, costs and limitations. Source prompts and raw requests/responses stay private. Public artifacts support CPU-only metric reproduction. The provider cutoff and final termination enforce the original cumulative budget below $10; provider credits do not increase that cap.
