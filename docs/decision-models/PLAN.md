# Frozen-weight decision models: Kev and Clef

Registered 2026-10-29, before benchmark inference. Status and amendments belong
in the run log; this protocol is preserved at registration.

## Question

Can two self-hosted decision models classify the same moderation examples as
Jev, and how do policy wording and a validation-selected cutoff change their
false blocks and missed violations? This is a practical extension of the policy
authoring study, not a controlled test of architectures or a claim about System 1.
There will be **no fine-tuning, gradient updates, or new ensemble fitting**.

## Models and interfaces

* `jaredpalmer/kev-4b`, revision `6cfce5c2fa4b4bd64026336ab649c5ca78857d52`;
  source `jaredpalmer/kev` at `2074cc44256200bb37540103fa4572901faa10f3`.
  Use its released Qwen3.5-4B-Base adapter and pointer head, native Choice input,
  and shipped temperature. Use the supported BF16 serving precision with merged
  adapter, Torch backend, no optional fused rewrite or CUDA graphs. The model
  card's published reference evaluations use FP32: record this difference.
* `Cloudflare/clef-flash`, revision `f0b7d3cd65296abfe459e6c228b618f5d8b26d2f`.
  Use the release's Qwen3.5-9B backbone **and joint schema decision head**, BF16.
  Generic chat/generation wrappers do not implement this classifier.

Each request contains one moderation question, with ALLOW and BLOCK criteria.
The state contains only `content`. Labels, provenance, and rationales are not
model inputs. Independent requests can be batched; different policies are
never bundled into a jointly evaluated Clef schema. Save full-precision head
probabilities and logits, without the public response helper's four-decimal
rounding. Do not interpret these probabilities as proven calibrated confidence.

## Populations and labels

Reuse the exact hash-verified Jev populations and label mappings:

| Benchmark | Fitting | Validation | Test | BLOCK means |
|---|---:|---:|---:|---|
| WildGuard | 1,024 | 512 | 1,699 | harmful user request |
| HateXplain | 1,024 | 1,920 | 1,924 | hate speech |

WildGuard tests **prompt harmfulness only**, not response harmfulness or refusal.
HateXplain merges normal and offensive-but-not-hateful posts into ALLOW. All
three splits are group-disjoint under the existing study's manifests. WildGuard
validation is sampled from WildGuardTrain, whose annotations and distribution
differ from the human-annotated official test. These public tests have already
been inspected in prior work; this extension is exploratory, not a fresh blind
benchmark. Publisher training overlap is not fully known.

## Policy development and freeze

For each model and benchmark, use the same three-candidate budget as Jev:

1. **Brief:** reuse Jev's short task question and two class definitions.
2. **Detailed:** reuse Jev's fuller scope, definitions, exceptions and precedence.
3. **Examples:** append four labeled fitting examples to the detailed policy.
   Select two BLOCK and two ALLOW examples from this model's detailed-policy
   fitting errors, with unanimous HateXplain labels preferred, then the same
   deterministic salted-ID ordering as Jev. Apply the same length and duplicate
   constraints; fall back to correctly classified fitting rows if necessary.

Run brief and detailed on fitting data, author and hash the example candidate,
then evaluate all three on validation. No manual candidate edits after examining
validation. Freeze model, code, candidates, and all selection choices before
uploading test data. Evaluate all candidates on test for a complete transparent
record, but never choose a winner by its test result.

## Selection and reporting

Use the existing comprehensive leaderboard's exact validation selection logic:
native decisions and thresholds 0.00–1.00 in steps of .01, plus an all-ALLOW
threshold above 1. Select for (a) balanced accuracy, (b) greatest recall with at
most 5% compliant errors, and (c) fewest compliant errors with at least 90%
recall. Preserve its deterministic tie-breaks and explicitly report infeasible
targets. Threshold selection changes the decision rule; it is not weight tuning
or probability calibration. Operating targets must be checked again on test.

Report balanced accuracy, ordinary accuracy, macro-F1, MCC, violation recall,
specificity, false blocks, missed violations, unresolved outputs, AUROC and
average precision. Show all policy variants at their native decision and with
their own validation-selected balanced cutoff to separate wording from cutoff
effects. Compute group-bootstrap 95% intervals (2,000 draws, seed 20261029),
including paired differences against Jev and appropriate previous leaders.
Intervals are descriptive and not adjusted for multiple comparisons.

## Integrity, feasibility and cost

* Validate native label order and finite probabilities; compare batched and
  single-request inference on fitting examples before bulk runs. Report maximum
  probability difference and any changed argmax; reduce batch size if needed.
* Never silently truncate inputs. Encode full inputs first and use a 16,384-token
  ceiling for the complete request. Count overflows and inference failures as
  unresolved errors, never remove them from metric denominators. Retry OOMs with
  smaller batches; stop on systemic adapter errors.
* Pin source revisions, record environment, input/policy hashes, timestamps,
  source checksums, stage freezes, costs, and provider shutdown evidence.
* Prefer GPU.ai's available 48GB GPU; RunPod is a fallback. Previous cumulative
  recorded spend is $12.92540555656 against the authorized $20 ceiling, leaving
  $7.07459444344. A $0.65/hour rental with six-hour automatic termination reserves
  at most $3.90 before any separately disclosed charges. Confirm the actual offer
  and disk charges before launch. Do not infer a renewed $20 allowance.
* Stop, sync evidence, and terminate before the provider deadline. Archive
  partial coverage honestly if time or budget is insufficient. No paid API calls
  are required. The run log must record actual usage and verified termination.

Primary sources: [Kev model card](https://huggingface.co/jaredpalmer/kev-4b),
[Kev source](https://github.com/jaredpalmer/kev), and
[Clef model card and release code](https://huggingface.co/Cloudflare/clef-flash).
