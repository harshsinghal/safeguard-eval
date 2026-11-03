# Methods: code representations and instruction search

## Models and representations

| Model | Role | Input and output |
|---|---|---|
| [Jina embeddings v2 base code](https://huggingface.co/jinaai/jina-embeddings-v2-base-code) | Frozen bidirectional code/text encoder, about 161M parameters | Masked mean of token states, L2-normalized 768-dimensional vector; no prefix |
| [Jina code embeddings 0.5B](https://huggingface.co/jinaai/jina-code-embeddings-0.5b) | Frozen Qwen2.5-Coder-derived retrieval model, about 494M parameters | Last non-padding token, L2-normalized 896-dimensional vector; publisher code-passage or QA-passage prefix |
| [Qwen3.5 4B](https://huggingface.co/Qwen/Qwen3.5-4B) | General LLM, policy-conditioned classification | Native chat template, no thinking, normalized next-token yes/no scores |
| [Qwen3.5 9B](https://huggingface.co/Qwen/Qwen3.5-9B) | Larger general LLM under the same search | Same decision interface and candidate policies |

The old Jina model is trained on code/text pairs and uses bidirectional attention.
The newer model adapts a code-generation backbone for retrieval. Its model card
specifies last-token pooling and task prefixes. We use `Candidate code snippet:`
for source files and `Candidate answer:` for skill documentation, fixed before
validation. Neither Jina checkpoint is a released malware classifier. Success
here would demonstrate a downstream trained head, not an inherent safety score.
Jina code 0.5B is CC-BY-NC-4.0; Jina v2 is Apache-2.0.

## What is learned

The labeled fitting sets train two separate heads per representation and task:
logistic regression and a one-hidden-layer ReLU MLP. Standardization uses fitting
vectors only. No Jina weights are updated. The MLP tries 128/256 hidden units,
two L2 strengths and three epoch checkpoints. Configuration selection averages
validation metrics across three seeds. The first registered seed is the primary
single-head result; the other two show initialization variability. This is not a
three-network prediction ensemble.

Qwen weights stay frozen too, but its development intervention is policy text.
It does not receive the fitting labels as a training objective. Six fitting
examples per task were inspected for development context. New examples in policy
text are authored descriptions rather than copies of labeled benchmark rows.

The previous Liquid baseline updates its whole encoder and classifier; TF-IDF
fits a vocabulary and linear decision rule. Comparisons therefore differ in
training and search, not just parameter count or attention architecture.

## What changed in the policies

The original brief, structured and evidence candidates are retained verbatim.
Three additions test distinct authoring changes:

| Candidate | Change | Reason for testing it |
|---|---|---|
| Behavior | Follow data reads, destinations, changes, authorization and disclosure; inspect secondary steps and all languages/sections | A benign-looking main feature can coexist with a malicious instruction |
| Contrasts | Add six paired descriptions: authorized vs covert transfer, scoped cleanup vs destruction, authentication vs theft, quoted vs active injection, honest vs fabricated reports, normal vs concealed setup | Dangerous capabilities alone do not establish malicious intent |
| Scope | Explicitly include authority overrides, hidden side effects and deception; retain exceptions for ordinary dependencies and missing context | Skill attacks can be instructions without a conventional malware payload |

Every candidate is tested with both Qwen sizes. Selection uses validation balanced
accuracy, macro F1, then shorter policy. The fixed score cutoff is 0.5. A yes/no
pair score is not a calibrated probability of real-world harm.

## Evaluation boundaries

The source-file task has 632 fitting, 240 validation and 160 test files. The skill
task has 1,024 fitting, 256 validation and 1,384 test texts. The input view remains
bounded to 8,000 source bytes, with a head/tail view for longer artifacts. No
additional tokenizer truncation is allowed. A text-only label can be ambiguous
when decisive package files or a clipped middle are absent.

Package/similarity groups protect the code split; publisher source separation
protects the skill split. Five skill families still overlap fitting and test,
covering 205 test records. Code labels are largely model-assisted. These limits
carry forward from the [data audit](../malicious-artifacts/METHODS.md).

All model choices freeze before new test inference. Prior aggregate test results
motivated this follow-up; test examples and their individual errors do not guide
authoring or fitting. Repeating this benchmark does not create a new independent
test sample. Report both errors, macro F1, MCC and grouped confidence intervals;
do not select a new winner after seeing test scores. Intervals are exploratory,
unadjusted and conditional on this benchmark and its labels.

The [dataset publisher](https://github.com/protectskills/MaliciousSkillBench)
also reports deterioration when detector evaluation holds out sources. This is
useful context for interpreting a development-to-test gap, not a direct ranking
against its baseline: our fitting sample, bounded text view and classifier
search differ. We do not establish which cue caused any particular failure.
