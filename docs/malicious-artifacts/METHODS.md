# What this comparison measures

The two decisions are **“Is this source file malicious?”** and **“Does this skill
direct malicious behavior?”** They are artifact-screening tasks. They do not ask
whether an employee is allowed to investigate malware or whether an agent can
safely execute a program in a particular environment. The same malicious file
could appear inside an entirely legitimate incident-response request.

## Populations and context

| Task | Fitting | Validation | Test | Test labels | Incomplete test views |
|---|---:|---:|---:|---|---:|
| OMCBench-derived code files | 632 | 240 | 160 | 80 benign / 80 malicious | 38 |
| MaliciousSkillBench source holdout | 1,024 | 256 | 1,384 | 545 benign / 839 malicious | 398 |

Code groups join members of the same package, identical model views and highly
similar views before splitting. The retained test has 101 such groups. The
code result is not directly comparable to the publisher's whole-package scores.
Some package-level threats reside in installation hooks or companion files that
a single source file does not contain. We use the file's own published label,
including benign files from malicious packages, rather than assigning every
file its package's label.

The skill test retains all 1,384 records from the official source-disjoint test
partition. Its sources do not appear in fitting or validation. Three fitting
and two validation source records have withheld original text and are excluded
before sampling; none of these five records belongs to the test. The publisher's
eight excluded identities stay excluded. Only the frozen skill text is supplied,
not additional files from the source package. The development samples are
class-balanced; the test keeps its original class mix.

A metadata audit before final inference found **five structural families shared
between skill fitting and test, covering 205 test records**. No structural
family crosses validation/test in the sampled populations. There is no exact
model-view overlap between partitions. We preserve the publisher's source
holdout rather than silently relabel it as an unseen-family test. Code has no
shared connected groups across fitting, validation and test.

Every model receives the same artifact view: at most 8,000 source UTF-8 bytes,
plus an omission marker when necessary. A long artifact contributes its first
6,000 and last 2,000 bytes. We retain its original label and count all decisions,
including failures, in the evaluation. This can hide the decisive evidence;
the full-view and clipped-view results therefore accompany the overall scores.
The publisher's native PolicyLM cleaner and windowing remain additional parts
of that evaluated system.

## How policies and classifiers are selected

For each prompted model, the three candidates change the decision specification:

| Variant | What changes | Practical question |
|---|---|---|
| Brief | A short malicious-behavior boundary and a benign exception | Can the model infer the intended distinction from a concise rule? |
| Structured | Enumerated behaviors, legitimate operations and exception precedence | Does explicitly separating theft, covert execution and sabotage from ordinary administration help? |
| Evidence | Additional action/target/destination checks and quotation/context distinctions | Does requiring concrete evidence reduce false blocks, or make the model miss threats? |

These candidates were written before validation. They are not corrections
derived from training errors and contain no copied dataset examples. Validation
chooses one candidate separately for each model and task. The study then compares
that choice with the brief baseline on test. It does not promote whichever
candidate happens to score highest on test.

PolicyLM uses native category fields; Shieldstral uses its instruction/query/
document wrapper; decision models use Choice schemas. Qwen uses a system prompt
with thinking disabled and normalized next-token scores for `yes` and `no`.
This last interface constrains the classification to two labels; it does not
measure the reliability of free-form JSON generation or a conversational agent.
All cutoffs are fixed before selection, including PolicyLM's publisher precision
preset. No model-specific threshold search, calibration or ensemble is added.
The preset name is not a guarantee of precision on a new task or policy.

The trained baselines answer a different implementation question. Character
TF-IDF learns a vocabulary and logistic classifier from fitting labels. Liquid
fine-tunes an encoder and binary head from those labels. Each has a separately
trained model per task and validation-selected hyperparameters. Neither receives
a policy at inference time. Their label use differs from the six prompted
systems, so a difference in scores does not isolate the effect of architecture,
parameter count or specialization.

## What the labels can establish

In this retained code population, label provenance is:

| Split | LLM annotation | Inherited from a benign package |
|---|---:|---:|
| Fitting | 403 | 229 |
| Validation | 141 | 99 |
| Test | 99 | 61 |

Although the upstream description discusses expert and LLM labeling, the
retained records have these two provenance tags. They are not an independently
human-adjudicated code test. Label inheritance can also miss a compromised
package assumed to be benign. Reported accuracy is agreement with source labels.

Skill labels consolidate several sources and evidence types. The release's
attack-category mapping is partial and overlapping. It can support descriptive
recall slices, but a missing category does not establish that behavior is absent.
Holding out sources tests a particular distribution shift, not every possible
new attack. Upstream model exposure to public artifacts is unknown.

The publisher also reports substantial source-holdout degradation and different
false-positive/false-negative trade-offs for its own text baselines and scanners.
Our fitting sample and bounded views differ, so those published scores are not
inserted into our leaderboard. See the [publisher's findings](https://github.com/protectskills/MaliciousSkillBench#detection-findings).

## Reading the leaderboard

Balanced accuracy gives equal weight to catching malicious artifacts and allowing
benign ones. False-block and missed-threat counts show how a score was achieved.
Unresolved responses stay in the denominator and are listed separately. A high
overall score cannot compensate for an unacceptable rate of blocking legitimate
software in a particular deployment.

The code test is small. Its uncertainty intervals cluster by package/duplicate
group; skill intervals cluster by supplied malicious structural family and benign
identity. Paired intervals compare policy variants on the same sampled groups.
They do not cover label uncertainty, unknown training contamination or fine-tuning
seed variation. The encoder experiment uses one registered seed. Ranking nearby
point estimates should not be described as establishing a winner.

## Execution record

All downloads were treated as inert data. No benchmark program or skill was
installed, imported or executed. Source files were read from regular archive
members in memory and verified against supplied hashes. Test inputs were withheld
from the GPU until all model selections were frozen.

The first CPU integration attempt failed because an inherited JSONL reader used
`splitlines()`, which treats Unicode separators inside JSON strings as line
boundaries. The study-specific reader now separates records only at ASCII
newlines. A regression test covers U+2028, U+2029 and U+0085. The original
registration and source are retained in amendment `001-unicode-jsonl`; this
repair changes neither the input text nor the policy/model requests.

Amendment `002-compressed-checkpoints` addresses limited local disk space during
collection. Selected FP32 weights are retained as losslessly compressed files;
verification hashes their original bytes. The GPU uses the original weights.
This storage change preceded selection freeze and test inference and changed no
input, score, model setting or selection rule.

A later local disk-write failure interrupted Jev test collection. Eight completed
API responses had not yet reached the prediction file, including two left in
temporary files before their billing settlement. All eight were recovered from
the original saved responses, with identity/schema checks and actual charges;
no replacement API calls were made for them and no result was discarded.
The remaining unrequested examples resumed under the same freeze. The public
recovery record and script preserve this execution incident. Runtime records are
diagnostic segments, not a latency or throughput comparison.

See the [plan](PLAN.md) for exact seeds, checkpoint revisions, optimization
settings, budget and selection rules.
