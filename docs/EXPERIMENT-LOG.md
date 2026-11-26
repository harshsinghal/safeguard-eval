# Experiment log

The complete, chronological record of every completed study, moved here from the
main [README](../README.md) so the landing page can stay short. Entries keep their
original numbers, selection objectives and wording; nothing below was re-scored.

## Experiment map

We started by asking whether a model could apply a platform's written rules. That led to three branches: **change the policy, change how scores become decisions, or learn a classifier from the model's internal features**. We also measure what it takes to serve representative systems. The map shows how the questions connect; it is not one shared pipeline. Numbers refer to the entries in the [experiment log](#experiment-log).

```mermaid
flowchart TB
    START["1–2 · Demo + injection<br/>Then benchmark moderation:<br/>WildGuard and HateXplain"]

    subgraph POLICY["Policy text and format"]
        P1["3–4 · Tune policies<br/>Specialists and Qwen<br/>WildGuard reference"]
        P2["5, 7 · Transfer + structure<br/>Model adapters<br/>Sections and examples"]
        P3["16 · Training-error edits<br/>Shieldstral → Qwen"]
        P4["22 · Relevant training examples<br/>Fixed / nearest / balanced<br/>Policy-only + neighbor-vote controls"]
        P5["23 · Optimize example use<br/>Model-specific fields · Embeddings<br/>Reranking · Diversity · Library coverage"]
        P1 --> P2 --> P3
        P2 --> P4 --> P5
    end

    subgraph SCORES["Scores and decisions"]
        S1["8–9 · Combine scores<br/>Calibration and cutoffs<br/>Probabilities / log-odds"]
        S2["10, 12 · Decision models<br/>Jev API · Kev · Clef<br/>Policy and cutoff tuning"]
        S3["13 · Decision ensembles<br/>Scores versus labels<br/>API + open / open-only"]
        S4["17 · Smart score ensemble<br/>Select complementary models<br/>Learn weights across families"]
        S1 --> S2 --> S3 --> S4
    end

    subgraph FEATURES["Representations and task classifiers"]
        F1["14 · PolicyLM + Qwen 0.8B<br/>Frozen representations"]
        F2["15 · Shieldstral + Qwen 4B<br/>Repeat with larger models"]
        F3["Both studies tested<br/>Layers, pooling, trained heads<br/>Single / combined features"]
        F4["18 · Task-specific classifiers<br/>PolicyLM + ModernBERT<br/>Linear / neural / contrastive"]
        F5["19 · Liquid encoder 350M<br/>Frozen linear control<br/>Fine-tune encoder + head"]
        F1 --> F2 --> F3 --> F4 --> F5
    end

    START --> P1
    START --> S1
    START --> F1
    P3 --> EVIDENCE
    P5 --> EVIDENCE
    S4 --> EVIDENCE
    F5 --> EVIDENCE
    EVIDENCE["11 · Balanced evaluation<br/>False blocks + missed violations<br/>Validate → freeze → test"]
    EVIDENCE --> SERVING["20 · Serving performance<br/>vLLM + native runtimes<br/>Batching · Caching · GPU cost"]
    SERVING --> CLOUD["21 · Cloud-compatible GPU<br/>L4 · vLLM and SGLang<br/>Prompt length · Loading checks"]
    EVIDENCE -.-> NEXT["PROPOSED · Not started<br/>Add trained feature heads<br/>Policy + cutoff · Second pass"]

    START --> INJECTION["24 · Injection detection<br/>Six models · Four collections<br/>Attacks + benign lookalikes<br/>Policy tuning · Fixed decisions"]

    INJECTION --> ARTIFACTS["25 · Malicious artifacts<br/>Code files + agent skills<br/>Native policies + trained classifiers"]
    F5 --> ARTIFACTS
    ARTIFACTS --> ARTREP["26 · Code embeddings + Qwen<br/>Frozen Jina · Linear / neural heads<br/>Six policies · Qwen 4B / 9B"]
    ARTREP --> CYBER["27 · Cyber assistance requests<br/>CyberSecEval MITRE + FRR<br/>Custom policies · Meta guard baselines"]
    ARTREP --> SKILLS["28 · Complete skill packages<br/>MalSkillBench · Companion-file ablation<br/>Policy models · Decision models · Jina heads"]
    SKILLS --> AGENT["29 · Agent behavior: StepGuard<br/>Pending action / completed run<br/>Native policies · Complete-context checks"]

    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#172c49;
    classDef policy fill:#eef4ff,stroke:#526b91,color:#172c49;
    classDef scores fill:#e9f5ef,stroke:#367556,color:#153e2b;
    classDef features fill:#f4efff,stroke:#7b63a8,color:#3d2c60;
    classDef proposed fill:#fff6e5,stroke:#a36e16,color:#61420f,stroke-dasharray:6 4;
    class START,EVIDENCE,SERVING,CLOUD neutral;
    class P1,P2,P3,P4,P5 policy;
    class S1,S2,S3,S4 scores;
    class F1,F2,F3,F4,F5,ARTREP features;
    class NEXT proposed;
    class INJECTION,ARTIFACTS,CYBER,SKILLS,AGENT policy;
    style POLICY fill:#f8fafc,stroke:#cbd5e1
    style SCORES fill:#f8fafc,stroke:#cbd5e1
    style FEATURES fill:#f8fafc,stroke:#cbd5e1
```

**How to read the map:** solid boxes describe completed work; dashed boxes describe proposed work or studies still awaiting completion. The separate **frontier-API pilot (6)** checked whether requests returned usable classifications; its full held-out experiment did not run. Not every branch covers both benchmarks: the first decision-model ensemble, the first two representation studies, training-error corrections, Liquid fine-tuning, and retrieved examples were tested on WildGuard only. The smart ensemble and task-specific contrastive-head study cover both benchmarks. The representation, correction, smart-ensemble, contrastive-head, Liquid, and retrieved-example studies use separate validation protocols and are **not merged into the common leaderboard**.

| Follow a branch | Where to start |
|---|---|
| Policy wording, transfer, structure, and examples | [WildGuard tuning](wildguard/METHODS.md) → [Qwen comparison](qwen-policy/READOUT.md) → [policy transfer](policy-transfer/READOUT.md) → [HateXplain structure tests](hatexplain/READOUT.md) → [training-error corrections](policy-corrections/README.md) → [retrieved examples](retrieved-examples/README.md) → [retrieval optimization](retrieval-optimization/README.md) |
| Scores, calibration, cutoffs, and combinations | [Probability ensembles](ensemble/READOUT.md) → [log-odds ensembles](ensemble-logits/RESULTS.md) → [Jev](jev/READOUT.md) → [Kev / Clef](decision-models/README.md) → [decision-model ensembles](decision-ensemble/README.md) → [smart ensemble](smart-ensemble/README.md) |
| Representations and task-specific training | [PolicyLM / Qwen](activation-probe/README.md) → [Shieldstral / Qwen](shield-probe/README.md) → [linear, neural and contrastive task classifiers](contrastive-heads/README.md) → [Liquid encoder fine-tuning](liquid-finetune/README.md) |
| Deploy and operate | [Seven-model serving study](serving/README.md) → [L4: prompt length and vLLM/SGLang](cloud-serving/README.md) · [Self-hosting implications](cloud-serving/DEPLOYMENT.md) |
| Test prompt and artifact security | [Injection and benign lookalikes](prompt-injection/README.md) → [malicious source files and agent skills](malicious-artifacts/README.md) → [code embeddings](artifact-representations/README.md) → [cyber requests and complete packages](cyber-skill-guardrails/README.md) |
| Judge agent behavior in context | [StepGuard: pending actions and completed runs](security-cognition/STEPGUARD-RESULTS.md) · [Native policy formats and edits](security-cognition/STEPGUARD-POLICIES.md) |
| Compare outcomes and see what is proposed | [Balanced metric guide](leaderboard/METRICS.md) · [leaderboard](leaderboard/CURRENT.md) · [next steps: reducing moderation errors](research-directions/REDUCING-MODERATION-ERRORS.md) |

The [smart-ensemble study](smart-ensemble/README.md) takes the next step: learn which native model scores help each other, then test the frozen combination. Adding trained representation heads to that combination, broader policy-and-cutoff optimization, and a targeted second pass remain [proposed work](research-directions/REDUCING-MODERATION-ERRORS.md), awaiting separate authorization.

## What we are testing

The main studies ask whether we can improve classification by changing the **policy, model interface, decision cutoff, or combination of models**, without further fine-tuning the language models. Some experiments fit calibrators, ensemble classifiers, or classifiers on hidden representations using labeled data. “No additional language-model fine-tuning” does not mean “no training data” or “no learned components.” A separate [Liquid encoder study](liquid-finetune/README.md) now tests **end-to-end supervised fine-tuning** against a frozen-encoder control, using prompts and labels rather than a policy document at inference time.

| Benchmark | Our decision task | Final test population |
|---|---|---|
| [WildGuardMix / WildGuardTest](wildguard/METHODS.md) | BLOCK harmful user requests; ALLOW benign requests. We evaluate **prompt harmfulness only**, not response harmfulness or refusal behavior. | 1,699 labeled prompts: 754 BLOCK, 945 ALLOW. The 26 prompts without a prompt-harmfulness label are excluded. |
| [HateXplain](hatexplain/README.md) | BLOCK hate speech; ALLOW normal and offensive-but-not-hateful posts under this particular rule. | All 1,924 official test posts: 594 BLOCK, 1,330 ALLOW. |

The main comparisons are binary ALLOW/BLOCK tasks. The earlier demonstrations also explored REVIEW, but these two benchmarks do not establish a validated three-way review workflow. The DiffusionDB browsing demo and synthetic demonstrations are separate from the main benchmark evidence.

The [dataset directory](datasets/README.md) covers all evaluation sources,
including the injection and jailbreak collections, original demonstrations,
source links, label mappings and study-specific splits. The
[model directory](models/README.md) lists the classifiers, general LLMs,
decision models, encoders, retrievers and API pilots, with their roles and interfaces.

| Model family | Models tested | How they enter the experiments |
|---|---|---|
| Specialist policy models | PolicyLM 1.7B, Shieldstral 3B, CoPE-B-A4B, GPT-OSS Safeguard 20B | Authored rules delivered through each model's native interface. |
| General-purpose LLMs | Qwen3.5 2B, 4B, 9B, 27B, and 35B-A3B | Classification instructions and policy text; thinking disabled in these comparisons. |
| Decision / “System One” models | Jev 1.14, Kev 4B, Clef-Flash 9B | Native classification interfaces. Jev was accessed by API; Kev and Clef were self-hosted from open weights. |
| Meta guard controls | Llama Guard 4 12B; Prompt Guard 2 86M | Llama Guard native/default and custom categories; Prompt Guard is a narrower injection diagnostic in the cyber/skill study. |
| Code embedding classifiers | Jina v2 code 161M; Jina code 0.5B | Frozen representations with task-trained linear and neural heads; separate code and skill populations. |
| Fixed-task reference | WildGuard 7B | The released fine-tuned model and official inference template; no custom-policy tuning arm. |
| Ensembles | Averages, learned weights, logistic regression, random forests, shallow gradient boosting | Combinations of specified component scores; the smart-ensemble study also selects a small subset using training folds. |
| Frozen-representation probes | Qwen3.5 0.8B with PolicyLM 1.7B; Qwen3.5 4B with Shieldstral 3B | Supervised logistic regression on individual or concatenated hidden states under a fixed harmfulness policy within each study; language-model weights stay frozen. |
| Task-specific classifiers | PolicyLM 1.7B and ModernBERT-base 149M | Matched linear, neural and contrastive heads on frozen features; separately trained on WildGuard and HateXplain with three neural seeds. |
| Supervised encoder fine-tuning | Liquid LFM2.5-Encoder-350M | Frozen encoder with logistic regression versus updating the encoder and a binary head; WildGuard only, three fine-tuning seeds. |

Not every model has been tested on every dataset. The [model directory](models/README.md), [interface audit](research-directions/POLICY-INTERFACE-AUDIT.md), and [decision-model study](decision-models/README.md) identify the checkpoints and adapters behind these names. Model size alone does not establish inference cost, speed, or suitability.

## Experiment log

The experiments follow the development of the research question. Each entry is named for what we tested; not every experiment improved the score. Earlier entries report their **original selection objective and metrics**. The leaderboard later in this page uses a common balanced-accuracy procedure; its selected configurations can therefore differ.

### 1. Custom platform rules: allow, block, or review

The project began with GPT-OSS Safeguard through Groq and a DiffusionDB prompt browser. We then compared four specialists on a fictional image-prompt policy with ALLOW, BLOCK, and REVIEW outcomes. On 48 synthetic test cases, Safeguard agreed with 40 draft labels, PolicyLM with 36, CoPE with 32, and Shieldstral with 19. CoPE matched all 32 clear binary cases but routed none of the ambiguous cases to REVIEW.

This made a practical distinction visible: classifying clear cases and handling uncertainty are different requirements. The labels were AI-drafted and await independent adjudication; this was a demonstration, not a validated safety benchmark.

[Original application and showcase](../DEMO.md) · [Evaluation design](../evals/README.md) · [Frozen results and predictions](../published_runs/2026-10-21/README.md)

### 2. Prompt injection: detecting instruction-boundary attacks

We tested instruction-boundary detection on 116 held-out Deepset examples and a separate 80-case synthetic challenge. PolicyLM reached 81.6% macro-F1 on the Deepset test; Safeguard reached 88.7% on the challenge. Those scores describe different populations and should not be averaged into one ranking.

Some public examples lacked the context needed to resolve the written rule. That shifted attention toward the benchmark itself: a model-policy disagreement can also expose a mismatch between policy intent and dataset labels. These were detection tests, not demonstrations of downstream attack prevention.

[Methods and label provenance](../evals/injection/README.md) · [Results, disagreements, and limitations](../published_runs/2026-10-24-injection/README.md)

### 3. WildGuard: tuning policy text with fixed model weights

We developed policy candidates using WildGuardTrain, selected configurations on validation, and evaluated prompt harmfulness on WildGuardTest. Edits clarified harm categories, allowed discussion, and which instructions took precedence. Model weights stayed fixed.

Shieldstral's ordinary test accuracy rose from **87.93% to 90.82%** with its selected text. A cutoff-only control reached 90.11%, showing why we cannot attribute every improvement to prose. The released WildGuard model scored 90.35%; the small difference from Shieldstral was uncertain. Other specialists improved less, and Safeguard's selected revision slightly regressed.

[Methods](wildguard/METHODS.md) · [Claims and limits](wildguard/CLAIMS.md) · [Policies, selection, and full results](../published_runs/2026-10-24-wildguard/README.md)

### 4. General-purpose LLMs: comparing nearby model sizes

We repeated policy-guided classification with five nearby-size Qwen models. The selected Qwen 2B configuration achieved 83.05% ordinary accuracy; Qwen 27B achieved 91.29%. In these studies, the small PolicyLM and Shieldstral specialists exceeded nearby-size Qwen configurations, while a larger Qwen remained competitive.

This supports considering small specialists alongside general models. It does not establish that specialization alone caused the difference, or that the searches found each model's best possible policy.

[Plain-language readout](qwen-policy/READOUT.md) · [What changed in the prompts](qwen-policy/PROMPT-CHANGES.md) · [Full results](../published_runs/2026-10-25-qwen/README.md)

### 5. Policy transfer: when a rule helps one model and hurts another

We developed revisions from each model's training feedback, then applied the selected texts to other models through their native adapters. A Qwen 2B-selected policy raised Shieldstral's ordinary accuracy from **87.82% to 90.76%**. In the other direction, the Shieldstral-selected text reduced Qwen 2B from **80.11% to 75.10%**. It also reduced PolicyLM from 85.05% to 74.57%.

These are comparisons within the transfer study, with its own candidate pool. They show that transfer can help or hurt. A successful policy is a candidate to test on a new model, not a guarantee of portable behavior.

[Transfer readout](policy-transfer/READOUT.md) · [Exact policy edits](policy-transfer/POLICY-CHANGES.md) · [Complete transfer matrix](../published_runs/2026-10-25-policy-transfer/README.md)

### 6. Frontier APIs: checking whether classification requests succeed

A separate pilot tested four frontier APIs with two reasoning settings on 32 fitting prompts: 256 observations. Some requests were filtered or produced unusable outputs. The full policy search and held-out comparison did not run within the available budget.

The lesson is operational: an API's ability to return the required classification is part of the system being evaluated. This pilot does not establish the accuracy ceiling of frontier models or justify adding them to the full-test leaderboard.

[Pilot findings](frontier-api/READOUT.md) · [Requests, failures, and costs](../published_runs/2026-10-25-frontier-pilot/README.md)

### 7. HateXplain: testing definitions, examples, and document structure

We moved beyond harmful requests to hate-speech classification. A common authoring document contained scope, definitions, blocking rules, permitted cases, exceptions, and examples. Model adapters mapped that content to native inputs: PolicyLM category fields, Shieldstral's prescribed wrapper, or Qwen's system instruction.

Removing the same four examples raised Shieldstral's ordinary accuracy from **52.4% to 61.0%**, but reduced Qwen 4B from **72.5% to 61.8%**. Reformatting the same clauses also changed outcomes. Removing PolicyLM's definitions increased accuracy while allowing **36 more hateful posts** through. The small automated wording revisions produced much smaller gains.

This supports testing both structure and substance, while checking which mistakes changed. It does not identify a universal policy format. Omitting sections also changes the information and document length, so these are not pure formatting effects.

[Readout](hatexplain/READOUT.md) · [Policy edits and component tests](hatexplain/POLICY-CHANGES.md) · [Native-interface audit](research-directions/POLICY-INTERFACE-AUDIT.md) · [Full results](../published_runs/2026-10-26-hatexplain/README.md)

### 8. Probability ensembles: calibration before combination

We compared probability averages, learned weights, logistic regression, and random forests. Before crediting an ensemble, we tested the individual models' decision settings. On HateXplain, changing Shieldstral's score-to-decision rule raised ordinary accuracy from **53.17% to 79.57%**, with no policy or model-weight change. False blocks fell from 885 to 177, but missed hate posts rose from 16 to 216.

Ensembles did not consistently improve on that calibrated single model. The mixed random forest reached 79.73%—only three additional correct cases overall. On WildGuard, a learned weighted average put 99.4% of its weight on Shieldstral. Combining models is an experiment, not an automatic upgrade.

[Readout](ensemble/READOUT.md) · [Methods and results](ensemble/RESULTS.md) · [Frozen evidence](../published_runs/2026-10-27-ensemble/README.md)

### 9. Log-odds ensembles: another way to combine scores

We reused the saved binary scores, converted them to log-odds, and fitted new combiners. These are **binary score transformations**, not access to every model's raw vocabulary logits.

The selected mixed logistic ensemble reached 80.82% ordinary accuracy on HateXplain; the specialist logistic ensemble reached 91.29% on WildGuard. The HateXplain gain still involved a trade: fewer false blocks and more missed hate than the strong calibrated Shieldstral reference. Language-model weights remained fixed, but the supervised combiners needed labeled fitting data.

[Results and error trade-offs](ensemble-logits/RESULTS.md) · [What we can claim](ensemble-logits/CLAIMS.md) · [Reproducible archive](../published_runs/2026-10-28-ensemble-logits/README.md)

### 10. Jev: policy tuning through a decision-model API

We tested Jev 1.14 through its native decision API with a brief policy, a detailed policy, and a detailed policy plus four training examples. It returned usable decisions for all 22,261 recorded classifications.

On HateXplain, ordinary accuracy at its native decision rule rose from **69.33% to 75.16%** across the brief-to-examples comparison. Selecting a higher cutoff raised accuracy further but missed substantially more hate. Jev was competitive without custom model fine-tuning; these results do not reveal its proprietary architecture or prove that “System One” is intrinsically better.

[Jev readout](jev/READOUT.md) · [Policy changes](jev/POLICY-CHANGES.md) · [API evidence and results](../published_runs/2026-10-29-jev/README.md)

### 11. Balanced evaluation: measuring both kinds of mistakes

We assembled the saved outputs into a common comparison, choosing configurations on shared validation examples rather than taking each model's highest observed test accuracy. **Balanced accuracy** gives equal weight to catching violations and correctly allowing compliant content. Separate views ask for a 5% false-block limit or a 90% violation-catch target.

For Jev on HateXplain, the balanced selection caught **79.12%** of hate posts versus 59.93% for the earlier accuracy-selected configuration, while false blocks increased from 134 to 297. The choice of metric changed which policy and cutoff were selected. The original 18-entry reanalysis is preserved; the next study extends it to 20 entries per benchmark.

[How selection works](leaderboard/README.md) · [Metric definitions](leaderboard/METRICS.md) · [Original reanalysis](../published_runs/2026-10-29-leaderboard/README.md)

### 12. Kev and Clef: testing open-weight decision models

Kev 4B and Clef-Flash 9B were self-hosted and tested with the same three policy types and benchmarks as Jev, without further fine-tuning. Kev selected the brief policy for both tasks; Clef selected the example-bearing policy with task-specific cutoffs.

On HateXplain, expanding Kev's brief policy reduced native balanced accuracy from **70.22% to 61.98%**. Clef's example policy scored worse at its native rule but better after validation-based cutoff selection. Their final balanced scores were 75.17% and 74.94%, versus Jev's 78.40%. More detailed policy text was not uniformly better, and policy and cutoff effects needed to be considered together.

[Study and deployment details](decision-models/README.md) · [Frozen runs](../published_runs/2026-10-29-decision-models/README.md) · [Expanded leaderboard](../published_runs/2026-10-29-leaderboard-decision-models/README.md)

### 13. Decision-model ensembles: combining Jev, Kev, and Clef scores

We fitted combinations of Jev, Kev, and Clef BLOCK scores on 1,024 WildGuardTrain prompts, selected settings on 512 separate validation prompts, and evaluated frozen choices on 1,699 WildGuardTest prompts. The primary probability logistic ensemble reached **89.32% balanced accuracy**, versus 88.69% for its selected Jev individual and 89.81% for WildGuard. It caught 27 more harmful prompts than Jev but made 22 more false blocks; the gain was uncertain.

The primary open-only Kev/Clef combination reached **87.52% balanced accuracy**. We also tested averages, learned weights, random forests, and decision-only controls. Retaining scores did not establish a clear advantage over combining decisions. The current leaderboard includes all nine combination methods for each of the two groups; selection aliases are not counted as additional methods. All scores were cached, so added GPU/API cost was $0. The example-bearing policies lacked fitting scores and were excluded from the new feature pool; no model weights or policy wording changed.

[Findings and error trade-offs](decision-ensemble/README.md) · [Registered plan](decision-ensemble/PLAN.md) · [Full results and reproducible archive](../published_runs/2026-10-30-decision-ensemble/README.md) · [Combined leaderboard](leaderboard/CURRENT.md)

### 14. Frozen representations: learning a classifier from two small models

We extracted hidden representations from Qwen3.5-0.8B and PolicyLM-1.7B under a fixed policy, then trained logistic regressions on 4,096 WildGuardTrain prompts. Settings were selected on 1,536 separate validation prompts and frozen before testing. **PolicyLM features alone reached 88.43% balanced accuracy**, versus **86.18%** for its fresh native-score control. Combining the two models reached **87.09%**; Qwen features alone reached **82.44%**.

Adding Qwen reduced false blocks by 11 but missed 29 more harmful prompts than the PolicyLM feature classifier. Earlier layers looked better on validation but did not consistently improve test performance. Native PolicyLM's AUROC was already similar, so the observed gain is at the selected allow/block rule. The experiment supports a useful task-specific readout, with labeled training data; it does not show that combining representations helps or that an adapted classifier will follow a newly edited policy. None of the new methods exceeded the archived WildGuard or specialist score ensemble. Compute cost was **$0.38**, and the GPU was terminated.

[Readable findings](activation-probe/README.md) · [Protocol and controls](activation-probe/PLAN.md) · [All metrics and settings](activation-probe/RESULTS.md) · [Frozen evidence](../published_runs/2026-10-30-activation-probe/README.md)

### 15. Shieldstral representations: does reading inside the model add value?

We repeated the frozen-representation approach with Shieldstral-1.0-3B and Qwen3.5-4B, adding direct output-score and score-combination controls. The same 4,096 fitting, 1,536 validation and 1,699 test populations were used. **Shieldstral's direct score reached 90.53% balanced accuracy**, its learned feature classifier 90.39%, and the combined feature classifier 90.35%. Adding Qwen corrected six mistakes but introduced seven compared with the Shieldstral feature classifier. The primary combination did not establish an improvement.

Choosing an earlier Qwen layer and a different pooling method on validation raised its test balanced accuracy from **83.93% to 88.81%**, but combining the selected representations still reached only 90.14%. Shieldstral's native validation score was 98.73%, falling to 90.53% on test; the gap was present even without a learned feature head. None of the 11 selections under either the 5% false-block profile or the separate 90% recall profile carried its respective target to test. The result supports testing the simplest native-score baseline before adding a learned head or another model. Cost was **$0.37**, and the GPU was terminated.

[Readable findings](shield-probe/README.md) · [Protocol](shield-probe/PLAN.md) · [Full results](shield-probe/RESULTS.md) · [Frozen evidence](../published_runs/2026-10-30-shield-probe/README.md) · [Follow-up: corrections from training errors](policy-corrections/README.md)

### 16. Policy corrections: do training mistakes lead to better rules?

We reviewed 58 Shieldstral training mistakes, froze four bounded policy revisions, and selected one on fresh validation. The chosen revision clarified permitted cases. We then transferred it unchanged to Qwen3.5-4B, selected each model's cutoffs, and evaluated an additional 2,048-example project holdout plus the reused WildGuardTest. No model weights or new classifier heads were trained.

**The revision did not improve Shieldstral.** Compared with the original policy's tuned cutoff, balanced accuracy went from **98.23% to 98.13%** on the additional holdout and **90.29% to 90.15%** on WildGuardTest. **Qwen improved from 88.85% to 89.77%** on the additional holdout, catching 30 more harmful prompts but falsely blocking 10 more legitimate ones. Its WildGuardTest change, **86.01% to 86.82%**, remained uncertain (paired 95% interval for the change: −0.04 to +1.63 points). Fixed-cutoff controls, unsuccessful candidates and newly introduced errors are also reported.

The useful finding is that a plausible correction can fail on its source model and help another interpreter. Policy edits need controlled evaluation; additional clauses and examples are not automatic improvements. The new holdout is unused in recorded project development but comes from WildGuardTrain's model-derived labels; it does not replace the human-labeled official test. None of eight separately selected operating-target configurations carried its respective target to WildGuardTest. Cost was **$0.72**, and the GPU was terminated.

[Readable findings](policy-corrections/README.md) · [Exact policy edits](policy-corrections/POLICY-EDITS.md) · [Registered protocol](policy-corrections/PLAN.md) · [Full results](policy-corrections/RESULTS.md) · [Frozen evidence](../published_runs/2026-10-30-policy-corrections/README.md)

### 17. Smart ensembles: learn which models help each other

We aligned seven native score sources on WildGuard and six on HateXplain, spanning specialists, Qwen and decision models. Five fitting folds selected a small combination and learned its coefficients; separate validation chose the decision cutoffs. Policies and backbone weights stayed fixed. We froze the choices before scoring the reused public tests and retained individual, equal-average, all-model, open-only and nonlinear controls.

On **HateXplain**, selection retained **Jev + Kev + Shieldstral**, reaching **79.97% balanced accuracy**. Compared with simply averaging all six models' log-odds, it made **48 fewer false blocks and four fewer misses**: a +2.14-point change (paired 95% interval +1.00 to +3.29). Against the validation-selected Jev individual at 78.42%, it made **86 fewer false blocks but 20 more misses**; that +1.55-point gain remained uncertain (−0.04 to +3.14). The predeclared all-model logistic and shallow gradient-boosting controls reached 81.03% and 81.08%, respectively; neither replaced the primary after testing.

On **WildGuard**, no added model met the fitting-fold improvement rule, so selection retained **Shieldstral alone at 90.53%**. The all-model logistic combination reached 90.43%. An equal log-odds average reached 90.91%, with seven fewer errors than Shieldstral, but the gain was uncertain. This supports measuring useful complementarity rather than assuming more model families will help. The low-false-block and high-recall profiles both missed their respective targets on WildGuardTest. On HateXplain, they met the targets with substantial tradeoffs.

The evidence includes all coefficients, rejected additions, component-removal checks, both error types and paired intervals. Accounted GPU/API cost was **$1.42**; the GPU was terminated. Both datasets reproduce on CPU from the published scores. These results use a separate validation protocol and remain outside the common leaderboard below.

[Readable findings and chart](smart-ensemble/README.md) · [How selection works](smart-ensemble/METHODS.md) · [Registered plan](smart-ensemble/PLAN.md) · [Full results](smart-ensemble/RESULTS.md) · [Frozen evidence and reproduction](../published_runs/2026-10-31-smart-ensemble/README.md)

### 18. Task-specific classifiers: does contrastive learning improve frozen features?

We trained logistic regression, a small neural network, and the same network with supervised contrastive loss on frozen PolicyLM and ModernBERT features. Each task used 4,096 fitting and 1,536 validation examples; neural settings were selected across three seeds. No backbone weights changed. **Contrastive training did not establish a consistent gain.**

On WildGuard, validation selected PolicyLM's contrastive head, but its primary test balanced accuracy was **84.78%**, versus **88.37%** for the linear control. It made 10 fewer false blocks but missed 62 more harmful prompts. All three contrastive seeds remained below the linear control. On HateXplain, validation selected PolicyLM's linear head at **78.01% balanced accuracy**; the contrastive head's primary 78.21% was an uncertain difference, and its three-seed mean was also 78.01%.

A separate accuracy-optimized HateXplain linear configuration reached **80.46% accuracy**, but missed 236 hate posts versus 113 at the balanced setting. This change includes regularization and cutoff selection. The task-specific heads require labeled data and have not been shown to follow newly edited policies without retraining. All 164 checkpoints reproduced exactly; extraction cost **$0.11**, and the GPU was terminated. These reused-test results remain separate from the common leaderboard.

[Readable results and all backends](contrastive-heads/README.md) · [Methods](contrastive-heads/METHODS.md) · [All seeds and operating profiles](contrastive-heads/RESULTS.md) · [Frozen evidence](../published_runs/2026-10-31-contrastive-heads/README.md)

### 19. Fine-tuning a Liquid encoder: learning a fixed moderation boundary

We fine-tuned Liquid's 350M encoder and a binary head on 4,096 WildGuard prompts, with 1,536 separate validation prompts. The control trained logistic regression on the same encoder's frozen features. Validation selected learning rate, epoch and cutoff across three seeds before the test prompts were uploaded. This time the encoder weights changed; no policy document was supplied at inference.

The primary fine-tuned run reached **86.40% test accuracy**, versus **82.22%** for the frozen control. It made **71 fewer errors**: eight fewer false blocks and 63 fewer missed harmful prompts. Across all three fine-tuning seeds, accuracy averaged **86.23%** (85.52–86.76%). The improvement over the frozen control was supported by a paired interval, but this bounded run remained below our earlier PolicyLM linear-head and released WildGuard results. It is a separate protocol, not an addition to the common leaderboard.

Validation accuracy was about 94%; test accuracy was lower. The validation-selected 5% false-block and 90% harmful-recall targets also failed on test. Fine-tuning improved this task-specific pipeline, but the labeling boundary, validation setting and deployment benchmark still matter. The readout includes default-cutoff controls and every seed, without substituting the best observed test result for the preselected result.

[Readable findings](liquid-finetune/README.md) · [All seeds and operating points](liquid-finetune/RESULTS.md) · [Registered plan](liquid-finetune/PLAN.md) · [Evidence and reproduction](../published_runs/2026-10-31-liquid-finetune/README.md)

### 20. Serving moderation: latency, batching and GPU cost

We served seven previously studied systems on one L40S: Shieldstral, Qwen and WildGuard through **vLLM 0.32.0**, and PolicyLM, Kev, Clef-Flash and the fine-tuned Liquid encoder through their native scoring implementations. We selected serving settings on 96 fitting prompts, then measured 384 separate WildGuardTest prompts three times at each load. Policies, weights and decision cutoffs stayed fixed.

At 32 requests in flight, shared-policy caching raised Shieldstral from **35.9 to 237.0 classifications/second**; Qwen had no prefix-cache hits and little change. Kev's optimized native runtime rose from **29.0 to 61.2/second**. The fine-tuned 350M Liquid classifier reached **358.4/second**, but it has a fixed learned boundary and no policy document at inference. Larger PolicyLM batches were rejected after score drift and an out-of-memory failure. Higher concurrency often increased waiting time, and some runtime changes shifted decisions near a cutoff.

These are deployment profiles, not an equal-accuracy model ranking. The readout explains latency, batching, sustained-load GPU cost and why an idle GPU changes the economics. The experiment cost **$1.65**; the GPU was terminated. The classification leaderboard below is unchanged.

[Plain-language findings and curves](serving/README.md) · [All operating profiles](serving/RESULTS.md) · [Plan and limits](serving/PLAN.md) · [Evidence and reproduction](../published_runs/2026-10-31-serving/README.md)

### 21. A cloud-compatible GPU: prompt length and engine choice

We tested **Qwen3.5 4B on one NVIDIA L4**, a GPU offered in AWS G6 and Google Cloud G2, rented through GPU.ai. vLLM and SGLang received identical input tokens, with the same policy and generation settings. Neither AWS nor GCP was accessed. Content lengths ranged from 64 to 4,096 tokens, plus a mixed workload; the policy and template added 402 tokens. Each engine selected a processing-chunk setting on separate fitting prompts before the length tests.

**The engines performed similarly; prompt length and queueing mattered much more.** A single short request took about 159 ms on vLLM and 157 ms on SGLang; a long one took 829 ms and 815 ms. At eight requests in flight, long-input median latency rose to roughly six seconds. A subsequent larger-chunk control did not improve throughput. These are small, warm, local-HTTP load tests, not production latency guarantees or new accuracy scores. One of 32 natural fitting labels differed between engines, reinforcing the need to recheck quality when changing runtimes.

A separate **Shieldstral 3B compatibility check** initially failed on SGLang's text-only setting and then its weight-loading path. Selecting the published Hugging Face-format files resolved the loader error: both engines passed the scoring check, agreed on all 32 serial labels, and showed very small score differences. That is interface evidence, not a Shieldstral speed ranking. Across the Qwen primary and control measurements, all **4,352 timed requests** returned valid classifications. The study cost **$0.62**; the GPU was terminated and temporary access keys removed.

[Findings and length curves](cloud-serving/README.md) · [Deployment implications](cloud-serving/DEPLOYMENT.md) · [All operating profiles](cloud-serving/RESULTS.md) · [Plan and amendments](cloud-serving/PLAN.md) · [Frozen evidence and reproduction](../published_runs/2026-11-01-cloud-serving/README.md)

### 22. Relevant examples: does retrieval improve a fixed policy?

We gave PolicyLM, Shieldstral, Kev and Jev either their existing policy, four fixed training examples, four nearest examples, or two nearest examples per class. A frozen E5 encoder searched 1,814 eligible training groups. Validation nominated a condition before all four were tested on the same 1,699 WildGuardTest prompts. Model weights and native decision rules stayed fixed; there was no new calibration or latency benchmark.

**Retrieval had different effects on different models.** Four nearest examples reduced ordinary accuracy from 86.70% to 84.34% for PolicyLM and from 90.82% to 89.70% for Shieldstral. It raised Kev from 87.52% to 88.17% and Jev from 89.29% to 89.46%, but those gains versus policy-only were uncertain. Validation selected policy-only for the specialists and balanced examples for the decision models; those balanced selections scored 88.11% for Kev and 89.76% for Jev, with intervals for their gains including zero. Neighbor voting alone scored 70.04%.

The errors explain more than accuracy alone. PolicyLM's nearest examples caught 57 more harmful prompts but created 97 more false blocks. Kev's selected balanced examples reduced misses by 36 while adding 26 false blocks. Jev's balanced examples reduced both errors, by only eight cases overall. The example library and retrieval rule need evaluation alongside the policy and its interpreter. This exploratory study cost **$0.875 of a fresh $20 allowance**; the GPU was terminated and temporary access keys removed.

[Findings and accuracy chart](retrieved-examples/README.md) · [All conditions and error counts](retrieved-examples/RESULTS.md) · [Retrieval diagnosis and proposed improvements](retrieved-examples/RETRIEVAL-AUDIT.md) · [Plan and amendments](retrieved-examples/NOTES.md) · [Frozen evidence and CPU reproduction](../published_runs/2026-11-01-retrieved-examples/README.md)

### 23. Smarter retrieval: format, embeddings, selection and coverage

We followed the initial retrieval study with four stages: model-specific example placement; E5, Qwen 0.6B/4B and BM25 retrieval; reranking, diversity, label contrasts and relevance gating; then a larger training library. Each classifier had 18 validation configurations. Choices were published before new test inference, with fixed model weights and output cutoffs.

**Better retrieval repaired some losses, but did not reliably beat policy alone.** PolicyLM's selected retrieval recipe rose from the original 84.34% to 86.52% test accuracy, still below its 86.70% policy-only control. Shieldstral's selected retrieval scored 89.94%, versus 90.82% alone. Overall validation selection retained policy-only for both. Kev selected diverse examples, but scored 87.35% on test versus 87.64% alone. Jev selected nearby label contrasts and scored 89.41% versus 89.29% alone—two additional correct cases, with the interval for its gain including zero. Kev's controls were recomputed serially after a fitting check and differ slightly from the preceding study.

All four selected retrieval recipes caught more harmful prompts **and** created more false blocks. Kev's balanced accuracy rose while ordinary accuracy fell, demonstrating why the error objective matters. Qwen 4B won none of the retriever comparisons, and no expanded-library condition became a final choice. This was a staged search on reused WildGuard data, not proof that retrieval cannot help. The follow-up cost **$1.821**, bringing the two retrieval studies to **$2.696 of the fresh $20 allowance**. The GPU was terminated and temporary access keys removed.

[Readout and chart](retrieval-optimization/README.md) · [All configurations and paired changes](retrieval-optimization/RESULTS.md) · [Plan and amendments](retrieval-optimization/NOTES.md) · [Pre-test selections](retrieval-optimization/freeze.json) · [Frozen evidence and CPU reproduction](../published_runs/2026-11-01-retrieval-optimization/README.md)

### 24. Prompt injection: attacks, obfuscation and benign lookalikes

Six models were compared on the original xTRam1 and deepset binary tests,
NotInject's benign lookalikes, and released JailbreakBench GCG/PAIR attempts.
The 2,697 final examples stay in separate comparisons: attack-only and benign-only
sets do not receive artificial balanced-accuracy scores.

The study compares brief, structured and example-bearing policies. Validation
selected examples for PolicyLM, Safeguard and Jev; structured for Shieldstral;
and brief for Kev and Clef. All selections were published before test inference.
The native decision rules remained fixed, with no new calibration, threshold
search or fine-tuning. Shieldstral's xTRam1 balanced accuracy rose from **71.66%
to 84.32%** after policy revision. Clef and PolicyLM finished near **95.3%**, but
Clef made one false block and 60 misses versus PolicyLM's 43 false blocks and 41
misses. PolicyLM detected 172 of 182 jailbreak attempts, while falsely blocking
26 of 339 NotInject benign cases. These trade-offs prevent a single pooled
security ranking. The readout retains uncertainty, failures and source-label limits.

[Study and findings](prompt-injection/README.md) · [Results and baseline changes](prompt-injection/RESULTS.md) · [Policy edits](prompt-injection/POLICY-CHANGES.md) · [Frozen evidence and reproduction](../published_runs/2026-11-02-prompt-injection/README.md)

### 25. Malicious code and agent skills across model families

Eight systems classify two kinds of artifact: source files and agent-skill text.
PolicyLM, Shieldstral, Qwen 4B, Kev, Clef and Jev each compare three prespecified
policies through their native interfaces. Separate Liquid 350M and character
TF-IDF classifiers learn from fitting labels. All selections were published
before final inference; no new calibration, cutoff search or ensemble was added.

PolicyLM's code balanced accuracy rose from **70.00% to
86.88%** with its selected evidence-focused policy. The
report shows the corresponding false blocks and misses: PolicyLM reduced false
blocks from 48 to 6 while introducing 15 misses. It also retains cases where
validation-selected policies regressed on test. Skill screening is a separate,
harder transfer in this panel: the source holdout and the bounded text view can
expose weaknesses that a code or prompt-injection score does not reveal.

The code test has 160 files and largely model-assisted labels. The skill test
retains 1,384 source-held-out records but shares some attack families with fitting.
These are static classification results, not proof of safe execution. Trained
classifiers use labels differently from frozen prompted models. Total GPU/API
cost was **$1.383**; the GPU was terminated. The two new
leaderboards remain separate from WildGuard, HateXplain and injection detection.

[Readout](malicious-artifacts/README.md) · [All scores, policy changes and uncertainty](malicious-artifacts/RESULTS.md) · [Methods](malicious-artifacts/METHODS.md) · [Pre-test selections](malicious-artifacts/preparation/README.md) · [Frozen evidence and reproduction](../published_runs/2026-11-03-malicious-artifacts/README.md)

### 26. Code embeddings and general LLMs for artifact screening

Can a small trained head make good use of code representations? We freeze two
Jina models—a 161M bidirectional encoder and a 0.5B Qwen-Coder-derived embedding
model—and fit separate logistic and one-hidden-layer neural classifiers for
source files and skills. Qwen 4B and 9B instead select from six policies, including
behavior checklists, paired benign/malicious examples and authority/scope rules.
All choices freeze before new test inference, with no output calibration.

The older Jina v2 model with logistic regression reaches **88.75%** code balanced
accuracy, matching Qwen 9B's observed score with a different mix of errors.
Jina code 0.5B with logistic regression scores **84.38%**
balanced accuracy on code and **57.26%** on skills; its
neural head scores **84.38%** and
**54.58%** using the first registered seed. All three
neural seeds are reported; none is selected by test performance. Qwen 4B's selected
policies score **86.88% / 54.85%**, and Qwen
9B's **88.75% / 55.48%** (code / skills).
None of the new systems improves on the earlier skill baseline.

These heads learn a fixed binary task from labels; they do not accept a newly
written policy at inference. The study therefore compares useful approaches,
not interchangeable capabilities. Code labels remain largely model-assisted;
skill sources are held out but some attack families overlap fitting. The report
retains both errors and grouped uncertainty. GPU cost was **$0.60**
against a $4 ceiling; the GPU was terminated. No paid model API was used.

[Readout](artifact-representations/README.md) · [Full results and seed sensitivity](artifact-representations/RESULTS.md) · [Policy changes and methods](artifact-representations/METHODS.md) · [Pre-test freeze](artifact-representations/preparation/README.md) · [Frozen evidence](../published_runs/2026-11-03-artifact-representations/README.md)

### 27. Cyber assistance: custom policies and Meta guard baselines

We adapt CyberSecEval MITRE and benign FRR requests into a binary classification
task. The 330 test requests are balanced and group-separated from development.
Seven editable models select among three policies; Llama Guard's default taxonomy,
Prompt Guard's fixed injection detector, and supervised Jina heads add controls.
This is agreement with source-derived labels, not Meta's native attack-generation
score or proof of a user's malicious intent.

Jev scores **83.33%**, Qwen 4B **60.91%**, and
Llama Guard's selected custom policy **77.27%** balanced accuracy.
Jina's logistic head scores **99.70%** after learning from fitting
labels; the primary neural head matches all 330 source labels. Because each label
comes from a different collection, the trained head may learn residual corpus
cues. This is **not evidence of perfect malicious-intent detection**.
Shieldstral and Jev both score **83.33%**, but Shieldstral has 18 false
blocks / 37 misses versus Jev's 7 / 48. All systems and intervals appear below. A source
formatting shortcut was repaired before testing, with original split assignments
preserved; remaining dual-use ambiguity and source differences limit the claim.

[Readout](cyber-skill-guardrails/README.md) · [Scores and policy comparisons](cyber-skill-guardrails/RESULTS.md) · [Pre-test selection](cyber-skill-guardrails/preparation/README.md)

### 28. Agent packages: does the model need companion files?

A separate MalSkillBench test contains 512 complete textual packages. Each prompted
model sees the full package, then SKILL.md alone under the **same selected policy**.
The 177 packages with companion files provide the direct comparison; 335 single-file
packages provide an identical-request repeat check. No package is executed.

Clef's selected policy raises skill-package accuracy from **80.86% to 90.82%**:
misses fall from 96 to 39 while false blocks rise from 2 to 8.
Jev scores **95.51%** on full packages and
**88.09%**
on SKILL.md alone. The results retain repeat variability as well as differences
caused by available evidence. The Jina document-only heads are trained separately,
so their comparison changes both the input and the fitted classifier.

Only three malicious test packages are wild; most are generated. This is a
different dataset from ProtectSkills/MaliciousSkillBench in experiments 25–26.
A higher score across those datasets cannot be attributed to adding companion
files. The paired test within this study addresses that question. Both studies
cost **$2.115** in total, including setup and preserved
failed attempts; the GPU was terminated.

[Readout](cyber-skill-guardrails/README.md) · [Paired results and uncertainty](cyber-skill-guardrails/RESULTS.md) · [Methods](cyber-skill-guardrails/METHODS.md) · [Frozen evidence and reproduction](../published_runs/2026-11-03-cyber-skill-guardrails/README.md)

### 29. Agent behavior: judge the next action or the whole run?

StepGuard changes the question from “is this request harmful?” to “is the agent's
behavior unsafe in this context?” Five models receive the same complete records.
We compare an initial policy with explicit judging criteria and with criteria
plus boundary examples. Each model/task chooses a policy on validation before
held-out inference. We do not tune model weights or decision cutoffs.

<!-- BEGIN STEPGUARD_TABLE -->
Balanced accuracy of each validation-selected policy:

| Model | Pending action | Completed run |
|---|---:|---:|
| Shieldstral 3B | 61.84% | 57.24% |
| GPT-OSS Safeguard 20B | 69.58% | 73.94% |
| Jev 1.14 (API) | 83.93% | 93.26% |
| Kev 4B | 66.26% | 68.57% |
| Clef Flash 9B | 65.73% | 77.78% |
<!-- END STEPGUARD_TABLE -->

<!-- BEGIN STEPGUARD_FINDINGS -->
Clef's criteria-plus-contrasts policy raises completed-run balanced accuracy
from **66.25% to 77.78%**: false flags fall from 114 to 60 and misses from 189 to
140. Kev improves from **61.75% to 68.57%** on that task, largely by reducing
false flags. The gains do not carry uniformly across tasks: Shieldstral retains
its initial policy, as does Clef for pending actions. Jev has the highest observed
balanced scores, but still misses **118 of 447 unsafe pending actions**. The
readout reports both error rates and uncertainty; a family label is not a
substitute for choosing an operating point against the relevant workflow.
<!-- END STEPGUARD_FINDINGS -->

The primary tests have **865 pending actions** and **894 completed runs**.
PolicyLM's published helper limits it to a separate matched short-record test;
all six models are compared on that subset in the readout. It has only seven
unsafe completed runs, so its results cannot support a broad long-context ranking.

These are derived grouped splits of StepGuard's synthetic SFT training material,
not official held-out or independently human-adjudicated tests. No dataset
action is executed and there is no REVIEW label. The record also preserves
Safeguard's runtime amendment and output variability. This study is separate
from the WildGuard/HateXplain leaderboard below.

[Results and error rates](security-cognition/STEPGUARD-RESULTS.md) · [What the policies change](security-cognition/STEPGUARD-POLICIES.md) · [Registered method](security-cognition/STEPGUARD-RUN-PLAN.md) · [Evidence and reproduction](../reports/stepguard-native/README.md)
