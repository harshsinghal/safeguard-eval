# CRM judgment curriculum v2: design proposal

Status: **draft for the owner's review, 26 November 2026.** Nothing has been generated or trained. Once agreed, this becomes a registered plan.

## Goal

Build a curriculum that teaches a small guard three things:
1. **What the action does.** CRUD, scope and egress, as in v1.
2. **When to be certain.** Allow or block confidently when the facts settle it.
3. **What kind of uncertainty it has, when it isn't certain.**
   - **Seek more context:** a missing fact would settle the decision. The guard names that fact. The system owner reads these results and fixes upstream tool calls, dry runs or prompts so the fact becomes available.
   - **Ask a human:** all the relevant facts are known, but the decision turns on values or compliance judgment that the policy leaves to a person.

The study holds the model fixed and varies the curriculum. v1 showed that the curriculum, not the base model, sets what the guard learns.

## What v1 taught us (the starting point)

- The tuned guard learned the three training policies but could not read a fourth: 48–55% exact on the unseen prose policy.
- It learned which facts make an action riskier: its decision moved the right way on 50 of 60 counterfactual pairs.
- It did not improve on objective questions about what an action does. In the staged arm, the semantics stage was overwritten by decision training.
- **A data bug in v1 is a lesson for v2.** In 36 probes, the reference label depended on a fact the input did not show. Training on items like that teaches the model to guess.

## What the research says works

| Finding | Source | What it means for this curriculum |
|---|---|---|
| A model can recall knowledge only if it saw that knowledge in **varied forms** (paraphrased, reordered). Seen in one form, it is memorized but not usable, and later fine-tuning doesn't fix that. | Allen-Zhu & Li, *Physics of LMs 3.1* (ICML 2024) | State each rule and principle in several forms: policy passage, FAQ, Q&A, worked case, contrast pair. One template per rule produces exactly v1's brittleness. |
| Training on **many free-form safety configs** lets a model follow a new config at inference time. | Zhang et al., *CoSA / CoSAlign* (ICLR 2025) | Train on dozens of generated policies that vary in style, structure, thresholds and persona, not three. Hold out policies by style **and** by content. This targets v1's biggest gap. |
| **Mixing formats** (zero-shot, few-shot, chain of thought) and task diversity improves held-out performance. Even 10% of a second format helps. | Longpre et al., *Flan Collection* (ICML 2023) | Mix the formats in one training run instead of sequential stages. That also fits v1's overwritten semantics stage. |
| **Easy-to-hard ordering is not a reliable win.** Results depend on the setting and on the difficulty metric. | Mixed recent studies (2023–2026) | Do not rely on stage ordering. Test it only as an ablation against a shuffled mix. |
| Training on **minimal pairs that differ only in the fact that matters** reduces reliance on spurious features. Gains are largest when data is scarce and level off with scale. | Kaushik et al. (ICLR 2020); Joshi & He (2021) | Build the curriculum around pairs and triples (see below). Expect a large benefit on a small dataset like ours. |
| **Ambiguous examples help most for out-of-distribution generalization.** Examples a model never learns are often label errors. | Swayamdipta et al., *Dataset Cartography* (EMNLP 2020) | Weight ambiguous examples more. Use training dynamics to find likely label errors and audit them. |
| Fine-tuning on answers the model **cannot know from its input** increases hallucination. | Gekhman et al. (EMNLP 2024) | Give a certain label only when the input shows the facts that decide it. Every other case becomes SEEK_CONTEXT. Enforce this in code (v1's 36 probes). |
| Training refusal on **unknown questions** teaches abstention as a skill that transfers across domains, and calibrates better than filtering at test time. | Diao et al., *R-Tuning* (NAACL 2024) | SEEK_CONTEXT can be taught directly as a label, not added as a threshold afterwards. |
| Models struggle to tell **"the input is ambiguous or incomplete"** apart from **"I can't work it out."** Synthetic data plus training improved this on 4B–8B models. | Ren et al., *UA-Bench* (ACL 2026) | This is the same split as SEEK_CONTEXT versus ASK_HUMAN. It is learnable, but each case must be labelled with the **reason** for its uncertainty. |
| The aleatoric/epistemic split is unstable in practice: ambiguity can often be resolved by asking. | Kirchhof et al. (2025) | Define the two uncertain labels **operationally**, by what would resolve them, not by an uncertainty theory. |
| Soft labels from **annotator disagreement** improve calibration and robustness under shift. | Several papers (2022–2025) | Keep the labelers' disagreement as a soft target on hard cases, and as a signal for ASK_HUMAN. |
| **Deferring to an expert** can be trained with a consistent cost-sensitive loss. | Mozannar & Sontag (ICML 2020) | Give each decision an explicit cost: a needless deferral costs reviewer time; a missed block costs harm. |
| Explanation traces and **reasoning over the written spec** help small models generalize. | *Orca 1/2* (2023); *Deliberative Alignment* (2024) | Worked cases cite the clause, then the facts, then the decision. Train on them with a language-modelling loss alongside the decision targets. |
| Guard accuracy on tool-call traces depends more on **parsing structured data** than on safety alignment. | *TraceSafe* (2026) | Keep the CRUD and effects stage, and give it more weight. |

## Decision space

The owner proposed four outcomes: allow, block, seek context and ask a human. v1 also has a policy-required approval, which is certain: the rule says an approver is needed. That is a different thing from a judgment call. **Proposed:**

| Decision | When | Output alongside |
|---|---|---|
| `ALLOW` | The facts and the policy say proceed | – |
| `ALLOW_LOG` | Proceed; the policy requires an audit record | – |
| `REQUIRE_APPROVAL` | The policy requires a second person (segregation of duties, thresholds). Certain. | The clause |
| `BLOCK` | The facts and the policy say no | The clause |
| `SEEK_CONTEXT` | A fact missing from the input would change the decision | **The missing facts** (from a fixed list) and who can supply them: the requester, a system lookup or a dry run |
| `ASK_HUMAN` | All the deciding facts are present, but the policy leaves the decision to discretion, two clauses conflict, or it turns on a values or compliance call | **The judgment question** (from a fixed list): policy conflict, discretionary exception, legal or regulatory interpretation, customer-harm trade-off |

v1's `CONFIRM`, where the requester confirms intent, becomes `SEEK_CONTEXT` with the requester as the source.

## How the labels stay objective

**Seek context: hidden-fact triples.** Every scenario is generated **complete** first, with all facts known. Then:
- with the decisive fact set to value A, the label is certain, for example `ALLOW`;
- with it set to value B, the label is certain, for example `BLOCK`;
- with the fact **hidden** from the input, the label is `SEEK_CONTEXT`, and the target names that fact.

A case is `SEEK_CONTEXT` **if and only if** two plausible values of a hidden fact lead to different decisions. The generator checks this rule directly: it runs the reference rules under each value.

Examples of decisive facts:
- whether the contract is signed;
- whether the recipient's domain belongs to the company;
- how many rows a `WHERE` clause matches;
- whether a deal is booked;
- who owns the record;
- whether the request came from the user or from retrieved content.

**Negative control, essential.** A hidden fact that does **not** change the decision (both values lead to `BLOCK`) must still get the certain label. Without these controls, a model can lower its loss by saying `SEEK_CONTEXT` whenever something is missing.

**Ask a human: designed judgment cases.** The facts are complete, but the policy sends the decision to a person. Families:
- **conflicting obligations:** a customer's deletion request against a legal hold or retention rule; a discount under the threshold but outside the pricing guidance;
- **discretionary exceptions:** "may be granted with business justification"; a justification is given, and someone has to weigh it;
- **interpretation:** whether data in a free-text field is personal data; whether a contractor counts as staff for an export;
- **trade-offs:** cancelling a renewal the customer disputes; writing off an invoice for a struggling customer.

Each family has **near-certain neighbours**: the same situation with the conflict removed, which becomes certain. That forces the model to learn what makes a case a judgment call.

**Checking ASK_HUMAN labels.** The two blind labelers see the complete case without the label. Where they systematically disagree on the certain decision, that supports ASK_HUMAN. Where they agree, the case is reviewed and may be reclassified. Their spread is kept as a soft target.

**Input-sufficiency check, enforced in code.** Each label records the facts it depends on. A build fails if any of those facts is absent from the rendered input. This closes the v1 bug.

## Data forms (the same principles, many surfaces)

| Form | Example | Loss | Share (initial) |
|---|---|---|---:|
| Action semantics Q&A | "Does this call delete records? How many? Is it reversible? Does data leave the company?" | decision | 20% |
| Decision cases | Policy + context + pending call → decision (+ missing fact or judgment question) | decision | 40% |
| Contrast pairs and triples | The same case with one fact changed or hidden | decision | (inside decision cases) |
| Worked cases | Clause → facts → decision → what would change it | language model | 15% |
| Policy passages | A rule explained in prose, with its rationale and edge cases, in several wordings | language model | 10% |
| FAQ | "Can a rep export their pipeline to a personal mailbox? No: deal amounts are financial data, and…" | language model | 10% |
| Policy reading | "Under this policy, what does a 30-record delete need?" across many generated policies | decision | 5% |

**Policies.** About 40 generated policies, varying:
- format: numbered rules, prose, a table, or an FAQ-style handbook;
- strictness and thresholds;
- persona and industry;
- clause order;
- the wording of the same rule.

Held out: 6 policies in unseen styles **and** 4 with an unseen combination of thresholds. The four v1 policies stay in the evaluation for comparison.

**Scenario coverage.** v1's 45 families are re-expressed under the new decisions, and new families are added for ASK_HUMAN and for hidden facts. The target mix of training decisions:
- about 50% obvious, certain cases, mostly benign, to keep the review rate realistic;
- about 20% ambiguous but certain;
- about 15% `SEEK_CONTEXT`;
- about 10% `ASK_HUMAN`;
- about 5% negative controls.

## Evaluation

The v1 test set, probes and live suite are kept, so results compare across versions. New measures:

**SEEK_CONTEXT**
- precision and recall;
- **missing fact named correctly**;
- false-seek rate on fully specified cases and on negative controls.

**ASK_HUMAN**
- precision and recall;
- the judgment question named correctly;
- the confusion between ASK_HUMAN and SEEK_CONTEXT, which is the attribution skill.

**Certainty**
- accuracy and confidence on the obvious slice; this should be near 100%, with high confidence;
- a risk–coverage curve.

**Policy reading**
- exact accuracy on held-out policies, by style and by content.

**Live**
- task success, harm and review burden, as in v1;
- plus the **context report**: the SEEK_CONTEXT outcomes grouped by missing fact. This is what the system owner would use to improve upstream tools. Score it by whether its top items match the facts the live tools actually omit.

## Experiments (one base model, curriculum varied)

| Arm | Curriculum |
|---|---|
| A | v1 data, relabelled into the new decision space (control) |
| B | v2 decision cases only (many policies, triples, ASK_HUMAN families) |
| C | B + semantics Q&A mixed in |
| D | C + worked cases, policy passages and FAQ with a language-modelling loss (**full v2**) |
| E | D with soft labels on disagreements |

- **Base model:** Shieldstral 3B, the same as v1. Optionally, run arm D again on Kev 4B to see whether the curriculum's effect carries over to another model.
- **Training format:** each decision is trained as yes/no queries in Shieldstral's native format. The missing fact and the judgment question are trained the same way, one query per named item.

## Budget and effort

- **Generation and reference labels:** local code, no API cost.
- **Blind labelling of the new test, probes and the ASK_HUMAN check:** about $6.
- **Live runs:** about $3.
- **Total:** within the roughly $16 left of the $25 budget.
- **Local GPU:** about 5 arms × about 1.5 h.

## Decisions for the owner

1. The decision space above: six outcomes, with `REQUIRE_APPROVAL` kept separate from `ASK_HUMAN`.
2. Whether to include the Kev 4B replication.
3. The ASK_HUMAN families: the four listed, or others that matter to you, such as sector-specific compliance.

## Sources

- Allen-Zhu & Li, Physics of Language Models 3.1: https://arxiv.org/abs/2309.14316
- Zhang et al., Controllable Safety Alignment (CoSA): https://arxiv.org/abs/2410.08968
- Longpre et al., The Flan Collection: https://arxiv.org/abs/2301.13688
- Kaushik et al., Counterfactually-Augmented Data: https://arxiv.org/abs/1909.12434 ; Joshi & He: https://arxiv.org/abs/2107.00753
- Swayamdipta et al., Dataset Cartography: https://arxiv.org/abs/2009.10795
- Gekhman et al., Fine-tuning on new knowledge: https://arxiv.org/abs/2405.05904
- Diao et al., R-Tuning: https://arxiv.org/abs/2311.09677
- Ren et al., UA-Bench (data vs model uncertainty): https://arxiv.org/abs/2604.17293
- Kirchhof et al., Uncertainty quantification needs reassessment: https://arxiv.org/abs/2505.22655
- Khurana et al., disagreement and calibration: https://arxiv.org/abs/2408.14141
- Mozannar & Sontag, Learning to defer: https://arxiv.org/abs/2006.01862
- Mukherjee et al., Orca: https://arxiv.org/abs/2306.02707 ; Orca 2: https://arxiv.org/abs/2311.11045
- Guan et al., Deliberative Alignment: https://arxiv.org/abs/2412.16339
- Chen et al., TraceSafe: https://arxiv.org/abs/2604.07223
- Curriculum ordering, mixed evidence: https://arxiv.org/abs/2510.19099 ; https://arxiv.org/abs/2308.05696
