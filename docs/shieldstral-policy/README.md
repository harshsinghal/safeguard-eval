# A shared Shieldstral adapter for moderation benchmarks

[Registered plan](PLAN.md) · [Reproduce locally](RUNNING.md) · [Prompt-free evidence](../../published_runs/2026-11-07-shieldstral-policy/README.md)

## Held-out results

Both shared adapters improved the equal-task score on the fixed binary
benchmark. The mixed adapter improved seven of ten primary tasks. The
contrast adapter also improved seven. Both failed the registered
cross-task gate because they missed more hate speech.

| System | Balanced accuracy | Paired change vs. base, 95% interval | Macro BLOCK recall | Macro false-block rate |
|---|---:|---:|---:|---:|
| Frozen Shieldstral | 70.93% | — | 68.62% | 22.79% |
| Mixed-task LoRA | **80.72%** | **+9.80 pp** [6.95, 12.65] | **82.70%** | 18.62% |
| Contrast LoRA | 79.97% | **+9.05 pp** [6.33, 11.77] | 80.50% | **17.92%** |

The headline averages the ten two-class tasks. The macro error rates use
all binary tasks with the relevant reference class. The mixed adapter
corrected 136 benchmark decisions and introduced 45 errors. The contrast
adapter corrected 139 and introduced 53. A common 0.5 cutoff gives 68.47%,
79.07% and 79.97% balanced accuracy, respectively.

| Task | Cases | Frozen | Mixed | Contrast |
|---|---:|---:|---:|---:|
| Pending agent action | 125 | 62.53% | 61.85% | 60.23% |
| Completed agent run | 125 | 44.85% | 87.99% | 90.42% |
| Cyber request | 63 | 84.17% | 89.01% | 90.62% |
| Harmful request | 63 | 92.09% | 90.47% | 90.47% |
| Hate speech | 63 | 56.25% | 69.81% | 59.93% |
| Deepset injection | 62 | 79.03% | 88.71% | 88.71% |
| xTRam injection | 62 | 82.26% | 93.55% | 91.94% |
| Complete skill package | 62 | 66.13% | 83.87% | 80.65% |
| Skill text | 62 | 53.23% | 54.84% | 58.06% |
| Source code | 62 | 88.71% | 87.10% | 88.71% |
| Benign lookalikes, ALLOW recall | 63 | 90.48% | 90.48% | 88.89% |
| Released jailbreak attempts, BLOCK recall | 62 | 95.16% | 100.00% | 100.00% |

The hate-speech models caught **31/31**, **21/31** and **11/31** hate posts,
respectively. Their false blocks fell from 28 to 9 and 5. That tradeoff
explains how balanced accuracy rose while both adapters failed the
10-point maximum drop in BLOCK recall. Pending-action balanced accuracy
also fell, even as BLOCK recall rose.

The descriptive ROC comparison at or below the frozen base's 22.79% macro
test false-block rate yielded 68.62% BLOCK recall for the base, 84.60% for
mixed and 83.43% for contrast. The separate operating points selected
against a 10% validation false-block target transferred to **14.02%**,
**12.96%** and **8.93%** false blocks on test. Their test BLOCK recalls were
55.87%, 75.95% and 71.55%.

At the validation-selected cutoffs, the frozen base, mixed adapter and
contrast adapter got **0/12**, **0/12** and **12/12** fresh policy-change
pairs fully correct. At a shared 0.5 cutoff they got **2/12**, **12/12**
and **12/12**. The contrast model retained the fixture behavior at its
selected operating point. Both adapters already had the same fixture
accuracy at the shared cutoff.

## Training and selection

The starting checkpoint is Mistral's Shieldstral-1.0-3B at revision
`003ec7e2b0bab5f0e6307edbaf186fa5822b76f5`. The run updates 4,685,824
language-attention LoRA parameters. The training target is cross-entropy on
the single native yes/no answer slot. The existing renderer supplies the
fixed policy and complete document. The one-step smoke test verified
canonical answer tokens, native score parity, finite gradients and identical
logits after adapter reload on a 2,043-token record.

The archived development pool has 3,316 fitting and 850 validation examples.
The registered audit protected the fixed suite and its 192 calibration
records. The 2,048-token training cap excluded 214 archived examples from
eligibility, concentrated in agent records, code and skill text. The mixed
adapter saw 32 ALLOW and 32 BLOCK examples from each of nine tasks. The
contrast adapter replaced four examples of each class per task with 36
two-policy pairs, preserving 576 examples, a balanced label distribution
and 72 optimizer steps per run. The 36 authored pairs have mechanically
derived labels. Their token counts and task mix differ from the replaced
records, so this comparison estimates the effect of the replacement package.

Both fits used one registered seed and one epoch. Frozen Shieldstral and the
two adapters scored all 850 validation cases with the same policy renderer.
The validation rule selected one global cutoff for each system. Validation
balanced accuracy was 74.29% for the frozen base, 85.50% for mixed and 85.40%
for contrast. Checkpoint and cutoff hashes were frozen before final inference.

## Scope

The 874 binary cases cover 12 tasks. Ten tasks have both labels and contribute
equally to the balanced-accuracy headline. The benign-lookalike and released
jailbreak panels each report their available-class recall. The two three-way
tasks account for the other 109 cases in the original 983-case suite. Scored
documents are complete within 16,384 tokens. Overflow and failed cases count
against their reference class.

The fixed suite is a reused public regression benchmark with inherited source
labels. The 12 separately authored policy-change pairs exercise new workflows,
rule wording and threshold boundaries. They have mechanical labels. Independent
adjudication and a fresh external source remain outside the evidence. The
bootstrap intervals measure paired group variation in the evaluated suite
conditional on this training seed.

The two PEFT adapters and source data are stored locally under ignored work
storage. The evidence archive contains reference and input hashes, decisions,
logits, metrics and resource records.

## Resources and verification

The smoke, development and held-out GPU stages took about 28.3 minutes in
total. Sampled device peaks were 51 C and 215.87 W across the stages.
Development peaked at about 8.76 GiB of PyTorch allocated memory. Sampled
device measurements include unrelated desktop and compute activity and
can miss short peaks. All study GPU processes exited. Provider spend was
$0, and local electricity was unmetered.

All 5,244 development and held-out scoring requests returned a score. The
offline audit reproduced the scorecard and checked the fixed case identities,
registered cutoffs, score-to-logit consistency and adapter hash records.
The first audit compared Python tuples with serialized JSON lists in the
operating points. The corrected verifier normalizes that representation
before comparison, using the same frozen predictions and scorecard.
