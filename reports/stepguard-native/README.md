# StepGuard: native policy and decision-model comparison

[Readable results](../../docs/security-cognition/STEPGUARD-RESULTS.md) · [Policy changes](../../docs/security-cognition/STEPGUARD-POLICIES.md) · [Registered protocol](../../docs/security-cognition/STEPGUARD-RUN-PLAN.md) · [Reproduction commands](../../evals/stepguard/README.md)

This bundle evaluates agreement with synthetic StepGuard SFT reference labels.
The two tasks are **pending-action safety** and **completed-run safety**. It is
a derived grouped test of public training material, not an official held-out
StepGuard benchmark, human-adjudicated enterprise test or live prevention study.
The released StepGuard checkpoint is not evaluated on its own training material.

## Frozen sequence

1. Parse the source into actor evidence, withholding reference reviewer judgments
   and rationales. Group related requests/history across both tasks, split, and
   count every native request without clipping.
2. Register three policy candidates and the selection rule. Evaluate validation.
3. Archive the incomplete Safeguard batch-16 validation pass, record the runtime
   amendment, and rerun its full validation at a ceiling of 64.
4. Freeze all model/task selections, then run initial and selected policies on
   test. Reuse initial predictions when validation selects the initial policy.
5. Calculate matched metrics, paired changes and grouped bootstrap intervals;
   collect outputs, delete paid resources and reconcile costs.

Registration was pushed in `750e201`; validation and selection were pushed in
`1adb86a` before test inference. These commits supplement the file hashes; no
test-selected replacement policy is reported.

| Artifact | SHA-256 |
|---|---|
| Source SFT file | `6429dc6f958e2b1fe242f2528dc6087c62e60e903263cf57dd88bc949752c90d` |
| Registration | `0ff3680dbe7b30b4827b8ddae0d983c6e9e4a703d3ef81ec9a8dc2d39b4f6ffb` |
| Selection freeze | `83b623f0b08350e4ea791d39a2764913cd167e8a25ba0ba46d3e88eb18b578d9` |

The source is `sft3k/agentguard_sft3k_sharegpt.jsonl` at
[dataset revision aadeae0](https://huggingface.co/datasets/ninty-seven/stepguard_data/tree/aadeae009800d8fbcd145575f1d1a6b37abb0950).
Its separate RL collection is not used. Publisher terms and third-party rights
still apply to any restored source material.

## Read the evidence

| File or directory | Purpose |
|---|---|
| [registration.json](registration.json), [authorization.json](authorization.json) | Original code/input hashes, selection rules and this run's bounded authorization; not permission for a reproducer to spend money |
| [data-audit.json](data-audit.json), [group-edges.jsonl](group-edges.jsonl), [metadata](metadata) | Source provenance, heuristic groups, split IDs, class/risk metadata; no raw source text |
| [context-audit.json](context-audit.json), [input-lengths.jsonl](input-lengths.jsonl), [eligibility.json](eligibility.json) | Full-input checks and explicit primary versus short-record populations |
| [policies](policies), [policy-token-lengths.json](policy-token-lengths.json) | Three authored variants per model/task, in native formats |
| [tokenizers](tokenizers) | Exact model/tokenizer/code-file hashes used for request counting |
| [selection.json](selection.json), [freeze.json](freeze.json) | Validation metrics, selected candidates and frozen evidence |
| [predictions](predictions) | Every scored validation and test prediction, including unresolved outputs; no reference rationale or raw input |
| [results.json](results.json) | Initial/selected metrics, paired changes, 95% grouped intervals and all recorded slices |
| [amendments](amendments), [superseded](superseded) | Preserved incomplete validation pass and operational repeat comparison |
| [runtime](runtime) | Package versions, serving settings, native runtime summaries and input audits |
| [jev-costs.json](jev-costs.json), [billing.json](billing.json), [cleanup.json](cleanup.json) | API accounting, GPU/storage cost and verified resource teardown |
| [published-manifest.json](published-manifest.json) | SHA-256 inventory of the published bundle, excluding this manifest itself |

## Comparison boundaries

The primary test has 865 pending actions and 894 completed runs. Shieldstral,
GPT-OSS Safeguard, Jev, Kev and Clef Flash share all those inputs. PolicyLM keeps
the released helper's single-window contract and fixed precision preset; its
supplement contains 234 actions and 99 completed runs. All six models are
reported on those same short test IDs. The other models retain policies selected
on the broader validation cohort. There are only seven unsafe short completed
runs, so that panel cannot support a broad ranking.

SAFE maps to ALLOW and UNSAFE to BLOCK. ERROR remains an incorrect unresolved
outcome; it is not credited as REVIEW. Source risk categories are not labels:
safe behavior can appear in a risky interaction. No threshold, ensemble or model
weight is fitted here. A source-derived test split does not rule out prior
exposure during a model publisher's training.

The bootstrap resamples heuristic scenario groups. Null intervals remain null
when a resample lacks a class. Intervals do not include policy-search, label or
runtime uncertainty. Safeguard's archived operational repeat had 19 binary flips
and two new unresolved outcomes on 163 overlapping validation records; all
reported selections and tests use the amended configuration. This overlap is
not a controlled estimate of batching effects.

## Reproduce safely

Start with the [implementation guide](../../evals/stepguard/README.md). Restore
source inputs into a private directory, verify hashes, and use the declared
native runtimes. Reading the published predictions and regenerating metrics
requires no paid inference. Repeating inference requires your own authorization,
provider credentials, budget and shutdown controls. Never execute any command
or tool call contained in a dataset record.

Raw source text, raw responses, private diagnostics, model weights, provider
identifiers, credentials and infrastructure access details are intentionally
absent. The result files contain enough labels and decisions to inspect the
reported errors without redistributing the source text.
