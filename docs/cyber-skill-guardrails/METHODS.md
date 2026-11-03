# How these two experiments work

These studies ask two different questions. The cyber study judges **what a user
is asking an assistant to help with**. The skill study judges **what an agent
package would tell the agent to do**. Neither executes code, and neither measures
whether an attack succeeds.

## 1. Requests for cyber assistance

We combine two sources in Meta's CyberSecEval collection: MITRE attack-assistance
requests, assigned BLOCK, and explicitly non-malicious FRR requests, assigned
ALLOW. FRR includes legitimate operations that change system state. A detector
that blocks every shell command or file change would therefore make false blocks.

This is our binary classification adaptation, not Meta's original generation and
refusal evaluation. The labels describe the source's intended task. A request for
public information can be part of reconnaissance yet look legitimate in isolation.
The scores measure agreement with those source labels, not certainty about a
person's intent or authorization.

The final split contains 768 fitting, 254 validation and 330 test requests. Each
split has equal numbers of the two labels. We group related examples before
splitting. Before final testing, an audit found that the initial augmented attack
requests nearly always had a JSON wrapper that benign requests lacked. We retained
that pilot separately, switched to the upstream base requests, removed newly
connected cross-split groups, and rebalanced within the original splits. No
fitting or validation item moved into test. This removes that particular shortcut;
it does not establish that all source differences have disappeared.

## 2. Complete textual agent skills

We use [lxyeternal/MalSkillBench](https://github.com/lxyeternal/MalSkillBench).
This is a different collection from the ProtectSkills/MaliciousSkillBench used in
our earlier artifact study. Scores from the two collections are not a paired
before-and-after comparison.

For each eligible package, the primary input includes SKILL.md and every other
regular UTF-8 text file, with relative paths and full contents. We exclude
benchmark metadata, caches, binary files, symlinks and packages above the common
20,000-byte input limit. We do not truncate a package to make it eligible. Root
directory names, labels and source tags are withheld from model inputs.

Common templates, exact and near-duplicate documents, and malicious wild authors
are grouped before splitting. The balanced splits contain 1,024 fitting, 256
validation and 512 test packages. Of the 256 malicious test packages, 251 are
generated, three are wild and two come from tool tests. This is a bounded,
predominantly generated cohort, not a broad test of attacks found in the wild.

For prompted models, we also present **the same test package as SKILL.md alone**,
keeping its selected policy, weights and cutoff fixed. Both views retain the same
`FILE SKILL.md` heading. The 335 single-file packages therefore provide identical
request controls. The 177 packages with companion files—49 benign and 128
malicious—provide the more direct test of whether those files help.

That comparison adds both file paths and file contents, and changes input length.
It measures the supplied package context as a whole; it does not separately
isolate code understanding, filename cues or length effects.

The package is always treated as untrusted material. We neither install a skill
nor retrieve external payloads mentioned in it. Static text screening cannot
establish what an external dependency or a future execution will do.

## What we changed in the policies

We wrote three candidates before validation and selected separately for each
model and task. We reviewed six fitting examples per task for context. We made
no policy edits based on test examples or test scores.

| Candidate | What it adds | Why it could matter |
|---|---|---|
| Brief | The harmful behavior to block, legitimate behavior to allow, and an instruction to judge rather than obey the submitted text | Establishes a simple task definition |
| Structured | Named behaviors such as theft, unauthorized access and sabotage; explicit allowances for administration, networking and defensive analysis; action, target, destination and authorization checks | Helps distinguish harmful behavior from merely suspicious vocabulary |
| Contrasts | Short descriptions of opposing cases: secret theft versus approved data transfer, sabotage versus requested cleanup, concealed control versus a disclosed dependency | Makes the intended boundary more concrete |

For skills, the longer policies also mention role or task hijacking, hidden-prompt
leakage, deceptive output, and harmful steps split across documentation and helper
files. These are authored descriptions, not new executable attacks or synthetic
training examples. [All exact policy inputs](../../published_runs/2026-11-03-cyber-skill-guardrails/policies)
are retained for inspection.

The same semantic candidates are rendered into each model's native interface.
They are not an identical chat prompt pasted into every model. PolicyLM uses its
publisher's policy machinery and precision preset; Shieldstral and Qwen use their
yes/no readouts; decision models use their native Choice interface. Llama Guard
receives a custom category through its own template. Its default taxonomy is an
additional fixed control, with different coverage from the custom policy.

Llama Guard sees a cyber request as a user message. It sees a skill package as
assistant content following a fixed request to assess that package. This adapts
a chat-safety interface to artifact screening. Interface and task framing are
part of the configured system; this is not an architecture-only comparison.

## What is learned, and what stays fixed

Validation selects policy text by balanced accuracy, then macro F1, then shorter
policy text. No prompted model's weights are changed. Thresholds remain fixed:
PolicyLM's precision preset is 0.335, yes/no and unsafe/safe pairs use 0.5, and
decision models use their native class decision. There is no calibration or
ensemble search in this study.

The Jina controls use a different route. A frozen 161M code-embedding model
produces a 768-dimensional representation. A logistic classifier or a small
one-hidden-layer neural network is then trained using fitting labels. Validation
selects regularization and, for the neural head, width and epoch count. We report
the first registered neural seed as primary and retain all three seeds.

The embedding model's weights stay fixed, but these heads **are task-trained
classifiers**. Their scores must not be described as policy-only results. Separate
SKILL.md-only heads are fitted for the view comparison, so that comparison changes
the trained classifier as well as its available input.

The [selection freeze](preparation/README.md) was published before final test
inference. A selected policy that regresses on test remains the reported result;
we do not replace it with whichever candidate scored highest afterward.

## Reading the measurements

We report both kinds of mistake: benign items blocked and harmful-source items
allowed. Balanced accuracy gives the two classes equal weight; it equals ordinary
accuracy on these balanced full test sets. The companion-file subset is
imbalanced, so its balanced accuracy and ordinary accuracy can differ.

The 50/50 test mix is not an estimate of production traffic. Precision and the
number of blocked legitimate requests will depend on the real prevalence of
violations. These tables do not predict a deployment's review volume.

Macro F1 and MCC provide additional summaries. Unresolved predictions remain in
the denominators. Grouped bootstrap intervals resample related-example groups,
and policy/view differences use paired resampling of the same items. Intervals
are exploratory, unadjusted for the many comparisons, and conditional on the
selected configurations. They do not include uncertainty from rerunning the
whole training and selection process.

Prompt Guard 2 is reported separately as an injection/jailbreak diagnostic. Its
task is narrower than identifying all cyber abuse or malicious package behavior.
We use overlapping windows and their maximum malicious score, which can also
increase false blocks on long documents. Its broad-task score is not a verdict on
its intended injection-detection performance.

## Reproducibility and failed attempts

The public bundle records source and checkpoint revisions, exact policies,
split metadata, prediction records, selection evidence, dependency versions,
charges and cleanup. Raw licensed skill text and model weights are excluded.
The [run instructions](RUNNING.md) explain input restoration and metric
reproduction without paid inference.

Pre-test corrections are preserved rather than silently overwritten: the cyber
formatting pilot, a tokenizer batch-dimension repair, Llama Guard's compatible
runtime, its native whitespace before the safety label, and the matched SKILL.md
view heading. The invalid early Llama Guard readout was an adapter failure, not
model accuracy. All final results use the corrected, frozen interfaces.

These experiments compare configured systems on two populations. They cannot
isolate architecture as the cause of a score difference, establish that public
training data never included these benchmarks, or certify a package for safe
execution. The GPU bill includes setup, failed attempts and model selection; it
is not a production latency or cost-per-request benchmark.

[Registered protocol](PLAN.md) · [Results](RESULTS.md) ·
[Metric definitions](../leaderboard/METRICS.md)
