# Policy interface audit and a bounded portability question

26 October 2026. Retrospective source audit and research proposal. No new model
inference, GPU rental, or paid API use was performed for this audit.

## What prompted the audit

The author asked whether different model-specific policy interfaces invalidate our
earlier experiments, whether PolicyLM's published comparisons use those interfaces,
and whether a common policy authoring format could work across models.

Required input packaging, recommended authoring practices, and the best-performing
policy are different questions. Earlier discussion did not distinguish them clearly
enough. The completed WildGuard, Qwen, and transfer studies already used native
adapters. That does not establish that their policies were optimal for each model.

## What the recorded experiments actually submitted

The audit inspected the archived runners, run manifests, saved policy candidates,
and publisher documentation at the checkpoint revisions recorded in the studies.

| Model | Recorded policy delivery | Scope of the evidence |
|---|---|---|
| PolicyLM | Upstream `Policy` and `Category` helper: `block` to `violation_rule`, `allow` to `not_violation_rule`, and `precedence` to `exception_override`; native policy validation, cleaning, and windowing | Native category interface, not a generic chat prompt. All harm types were grouped into one broad category. |
| Shieldstral | Publisher's fixed system instruction; policy in `<Instruct>`, a fixed BLOCK question in `<Query>`, and submitted content in `<Document>` | Native yes/no interface. The policy body and fixed question are separate. |
| CoPE-B-A4B | Task instruction followed by POLICY, LABELS, and CONTENT sections in a user message through the checkpoint's chat template | Native binary classification framing. |
| GPT-OSS Safeguard | Policy in the system message; submitted content in a separate user message; a fixed JSON output instruction | Policy and content have separate message roles. |
| Qwen | System classification instruction and policy; separate user content; fixed A/B output mapping, with thinking disabled | General-purpose instruction model receiving an explicit classification task. |
| WildGuard | Official fixed-task completion template and slow-tokenizer input IDs with one BOS | Fixed-task baseline; no authored-policy optimization arm. |

Relevant implementation: [shared adapters](../../evals/run.py),
[WildGuard-study runner](../../evals/wildguard/run.py),
[Qwen runner](../../evals/qwen_policy/run.py), and
[transfer runner](../../evals/policy_transfer/run.py). Archived copies are in each
study's `published_runs/.../source/evals/` directory.

The adapters did not consume every field identically. PolicyLM did not separately
consume `purpose` or `review`; Qwen included `purpose` but not `review`. This was
explicitly recorded in the original [lab notebook](../wildguard/NOTES.md), before
the shared candidate search. The edited substantive fields—`block`, `allow`, and
`precedence`—were consumed by every adaptive model. Across all 11 saved WildGuard
candidate texts and the transfer study's baseline plus 20 revisions, `purpose`
and `review` each remained constant. The studies did not isolate the effect of
those different fixed task wrappers.

The final WildGuard tokenizer setup was repaired during the pilot and documented
before the main comparison. Initial pilot artifacts remain in the archive; they
must not be represented as having identical runner code to the final experiment.

### Source checks

- WildGuard study: all 84 manifests match the archived shared adapter hash; 79
  match the archived final runner hash. The five differing runner hashes belong
  to the initial pilot runs. All 12 test-run manifests match both final hashes.
- Qwen study: all 332 recorded source hashes across 83 manifests match the
  corresponding archived files.
- Transfer study: all 1,036 entries in source maps across 98 manifests match the
  corresponding archived files. The four remaining copied specialist baseline
  manifests also match both recorded runner and shared-adapter hashes.

These checks connect the inspected code to recorded runs. They are not a new
inference replication or proof that every possible integration issue is absent.

### Pinned documentation checked

| Publisher model | Checkpoint revision |
|---|---|
| [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b) | `b3b2cd408a08a68ab6a30c1fc1e440204e44d57e` |
| [Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B) | `003ec7e2b0bab5f0e6307edbaf186fa5822b76f5` |
| [CoPE](https://huggingface.co/zentropi-ai/cope-b-a4b) | `b28a1c734eff80d82e5df7964c7dfd0de8509900` |
| [Safeguard](https://huggingface.co/openai/gpt-oss-safeguard-20b) | `8a11e17b25c973a24099d4016bf2e17dd7ec1574` |

PolicyLM's authoring guidance recommends short rules separated by violation type.
Our broad harmfulness category uses its supported interface but does not test that
recommended decomposition. A category-decomposition arm would also need to specify
how per-category scores produce the final decision; it is not merely a punctuation
or Markdown change. Its recommended cutoffs differ from our preregistered primary
0.5 cutoff; we also ran validation-based cutoff controls. Neither choice should
be described as universally optimal.

## What survives, and what needs qualification

1. **Within-model editing evidence survives this concern.** In the tested
   configurations, changing policy rules while holding weights and the native
   adapter fixed changed decisions. Improvements were not universal, and some
   small differences were uncertain. This supports testing authored policy as an
   operational input; it does not establish an optimal policy or a mechanism.
2. **Transfer evidence concerns policy content through fixed adapters.** The
   findings show that a selected rule text can help or hurt another model under
   the recorded configuration. They do not show transfer of an identical complete
   model input, nor that native-interface differences have been experimentally
   eliminated as contributors to cross-model outcomes.
3. **Rankings apply to tested configurations.** The studies do not establish each
   model's performance ceiling, intrinsic architecture superiority, or the result
   of an exhaustive search over native formatting, category granularity, cutoffs,
   and wording. These qualifications belong beside any model comparison.

Different interfaces alone do not justify discarding or rerunning every result.
An actual integration defect would require identifying and rerunning the affected
conditions. Better native authoring is a new, separately labelled comparison; it
must not replace historical inputs or results retroactively.

## What PolicyLM's published comparison discloses

Its [custom-policy table](https://huggingface.co/musubilabs/policylm-1.7b#custom-policies)
describes shared policy text on synthetic business policies. The footnotes specify
different request arrangements for Safeguard and CoPE, so shared text does not mean
identical invocation. Its separate generic-safety table uses another methodology.

The model card and model repository inspected here do not provide a complete
competitor evaluation harness or every rendered competitor prompt. We therefore
cannot independently confirm the interface fidelity or optimization effort for
Granite Guardian, SingGuard, or every other comparator. This is a reproducibility
limit, not evidence that their comparison is invalid. The card also discloses
development use of evaluation sets, which limits treating those results as unseen
confirmation.

## A useful portability proposal

Investigate a **common authoring specification with model-specific adapters**.
Do not promise that one raw prompt works equally well everywhere or claim novelty
for structured policy authoring without a separate related-work review.

The common source can contain a version, scope, definitions, rule identifiers,
violation conditions, permitted cases, exceptions and precedence, and labelled
examples. Keep machine output instructions and deployment decisions explicit.
An adapter maps supported components into a model's native fields or messages.
Preserve clause text where possible and record any required transformation.
Adapters must report unsupported features or excessive length rather than silently
dropping a rule. A fixed-taxonomy model may not support arbitrary authored rules.
For binary models, REVIEW requires a separately defined workflow rule; a shared
schema cannot create a native third class or calibrated uncertainty.

Two distinct checks are necessary:

- **Representation:** did every required clause, exception, and example reach the
  model through a supported interface, within its input limits?
- **Behavior:** did the model apply the intended rules on labelled cases? Preserving
  text does not guarantee preserving decisions across models.

This builds on our existing policy JSON and adapters. The research contribution
would be measuring the benefits and limits of that separation, not merely inventing
new Markdown headings.

### Small next test

Refine the existing [HateXplain proposal](STRUCTURED-POLICY-STUDY.md) without adding
another dataset or a large model panel. Keep PolicyLM, Shieldstral, and Qwen-4B.

1. Author one common, structured policy grounded in annotation guidance and training
   data. Register its scope and component-to-model mapping before evaluation.
2. Deliver it through verified, fixed native adapters and measure its held-out
   behavior. Freeze rendering choices before comparing wording.
3. Give each model the same bounded training/validation revision budget, retaining
   the same intended rules. Record any departures from native authoring guidance.
4. Transfer the selected substantive rules through the same adapters, with no
   recipient-side rewriting or selection. Compare missed hate, false blocks of
   offensive-but-not-hateful posts, normal-post false blocks, and paired case
   changes alongside aggregate metrics.

The question is: **How much performance is retained when one policy source is used
across models, compared with separately tuned versions of the same intended rules?**
The separate presentation and omission comparisons in the existing proposal still
require matched information and explicit treatment-delivery checks. Do not attribute
a gain to formatting when new rules or examples were added at the same time.

Policy owners review intent, exceptions, and examples. Engineers verify translation,
measurement, and regressions. Together they decide whether the maintenance benefit
of a shared source justifies any measured performance trade-off. Results may support
portable authoring for the tested models and task; they cannot establish universal
compatibility or guarantee identical behavior.
