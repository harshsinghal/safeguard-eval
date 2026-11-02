# What changed in the injection policy?

The three candidates ask the same question: does this submitted text try to
redirect an AI across an instruction boundary or evade an AI restriction?
This differs from asking whether a topic is harmful. All model weights and
score-to-decision rules stay fixed.

| Candidate | What the author supplies | Why test it? |
|---|---|---|
| Brief | A short definition of overrides, restriction bypasses and hidden-information extraction, with an exception for ordinary questions and discussion of attacks. | Establish a usable starting policy. |
| Structured | Explicit mechanisms: impersonated authority, unrestricted personas, encoded instructions and adversarial suffixes. More precise allowed cases: translation, programming, harmless roleplay and analysis of quoted attacks. | Test whether clearer boundaries improve decisions without turning suspicious words into a blocklist. |
| Structured plus examples | The structured policy and four complete, labeled fitting examples, two per class. Each model's brief-policy mistakes have priority. | Test whether concrete boundary examples help that particular interpreter. |

For example, the structured policy says: “Non-English words, symbols, encoding,
and words such as ignore or bypass are not sufficient evidence by themselves.”
That sentence is an allowance, not a guarantee that a model will follow it.
We also say that an attack attempt counts even if it would fail. Otherwise a
classifier might confuse detection of an attempt with prediction of its success.

The examples are selected by a fixed procedure from the 256 fitting records.
They are at most 280 characters, come from distinct similarity groups and are
ordered by a stable hash. Correctly classified fitting examples fill any missing
slots. Neither validation nor test examples are copied into the policy. Their
source IDs, labels and the model's initial decisions are published; exact quotes
can be restored privately from the pinned data.

The four copied examples were balanced by label, not by source. The fixed
selection procedure chose four deepset examples for five models; Jev received
three deepset examples and one xTRam1 example. This concentration and the short
length limit constrain what we can infer about few-shot guidance more generally.

## Same intent, different model interfaces

| Interpreter | How the policy is delivered |
|---|---|
| PolicyLM | One category with violation, non-violation and exception fields. Fields are single-line; quoted example data stays escaped. Its standard cleaner and long-message handling remain enabled. |
| Shieldstral | A rule in the publisher's instruction/query/document wrapper, evaluated through its yes/no token pair. |
| GPT-OSS Safeguard | A system policy with JSON-quoted content and an exact binary JSON output contract. |
| Jev, Kev and Clef | Native Choice questions with instructions and separate ALLOW/BLOCK criteria. Examples attach to the relevant criterion. |

We select among these three candidates separately for each model, using the same
256 validation examples. Selection rewards the average of catching attack labels
and allowing benign labels, equally across the two development sources. It does
not reward the highest test score, and it does not optimize specifically for the
external NotInject or JailbreakBench collections.

When the example-bearing policy is selected, its test comparison with brief
changes both the detailed guidance and the examples. That comparison cannot
isolate which component caused a gain. Validation evaluates all three candidates,
but this is not a full held-out component-ablation study.

“Structured” changes both the amount of guidance and its specificity. It is not
a pure Markdown-formatting experiment. The example-bearing policies differ
between models, so this is also not a policy-transfer experiment. The published
source labels have ambiguities; copying their examples can teach those
ambiguities too. A larger or more detailed policy may improve one error type
while worsening another, or fail to carry a validation gain to the test set.

[Exact policy definitions](../../evals/prompt_injection/policies.py) ·
[Study design](PLAN.md) · [Restoration instructions](RUNNING.md)
