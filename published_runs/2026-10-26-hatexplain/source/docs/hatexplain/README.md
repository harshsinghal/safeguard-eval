# HateXplain: structured authoring, omissions, and policy transfer

This follow-up asks how an authored policy behaves when its presentation, components,
or wording change, and whether selected wording travels across native model interfaces.
It extends the earlier WildGuard work to a narrower governance decision: block hate
speech while allowing offensive-but-not-hateful and normal posts under this policy.

- **[Start with the plain-language findings](READOUT.md).** The same examples and
  presentation changes had different effects across models. Wording optimization
  produced only small or negligible gains in this bounded search.
- [Complete results and reproducible evidence](../../published_runs/2026-10-26-hatexplain/README.md).
- [Prospective plan](PLAN.md): data, interfaces, comparisons, selection, metrics, budget.
- [Lab notebook](NOTES.md): execution, failures, and decisions in order.
- [Authoring amendment](AUTHORING-AMENDMENT.md): failed editor outputs and the repaired contract.
- [Scope review](SCOPE-REVIEW.md): which drafts were eligible before validation.
- [Exact policy changes](POLICY-CHANGES.md): before/after text for selected and rejected revisions.
- [Data manifest](data-manifest.json): pinned sources, duplicate quarantine, and exact populations.
- [Progress](progress.json): current stage and spending.

The three classifiers are PolicyLM 1.7B, Shieldstral 3B, and Qwen3.5-4B. The common
source contains scope, definitions, blocking rules, permitted cases, exceptions,
and four training demonstrations. The native adapters preserve its active clauses;
they do not send identical complete model inputs. PolicyLM's field interface is
excluded from the whole-document Markdown/linear/tagged/order comparison.

The shared policy, all omissions, and every document format are predefined. Policy
revision uses training examples only, and selection uses validation only. A frozen
run matrix precedes test upload. Definitions of ALLOW and BLOCK here describe this
one hate-speech rule, not a complete platform policy. REVIEW is not evaluated.

The initial editor failed six times by echoing its input. A documented amendment
added six calls with schema-constrained editable text. The search produced limited
diversity, and scope review excluded two inconsistent drafts and one duplicate.
These limitations are part of the evidence; the experiment does not establish an
optimal authoring method or each model's best attainable performance.

## Reproduction

The [public evidence bundle](../../published_runs/2026-10-26-hatexplain/README.md)
provides exact policies, source/configuration hashes, complete prediction records,
selection/freeze records, and CPU reproduction of the metrics and paired intervals.
This verifies recorded evidence; it does not rerun the neural models. Private
submitted-post and editor-feedback traces remain local. Four licensed training
demonstrations are included in the policy artifacts.

All 45 runs completed: nine fitting runs, six validation runs, 27 full-test
conditions, and three 256-post repeatability checks. The 73,452 classifications
had no output failures. GPU.ai billed $1.34, taking cumulative spending to $12.12
of the authorized $20. The instance and temporary SSH key are removed; RunPod
was not needed.

Inference entry point: `evals.hatexplain.orchestrate`. It assumes the pinned Linux
GPU environments and localhost model service described by the earlier transfer
study. The amended editor is `docs/hatexplain/editor_repair.py`; it is separately
registered and never silently substitutes for the failed original calls. Use the
saved registry, data hashes, protocol, amendment, and scope review when reproducing
the procedure. Repeating inference on another runtime can change close decisions.

Sources: [HateXplain on Hugging Face](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain),
[publisher repository](https://github.com/hate-alert/HateXplain),
and [Mathew et al., AAAI 2021](https://arxiv.org/abs/2012.10289).
