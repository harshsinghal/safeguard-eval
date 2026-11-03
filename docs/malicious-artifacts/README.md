# Screening malicious code and agent skills

This study extends policy authoring research to malicious source files and agent
skills. It compares two policy models, three decision models, a general-purpose
Qwen model, a fine-tuned Liquid encoder and a text-feature classifier. These are
static screening tasks; no downloaded code or skill is executed.

See the [registered plan](PLAN.md). Results are pending execution.

The prepared code subset has **632 fitting, 240 validation and 160 test files**.
The prepared skill study has **1,024 fitting, 256 validation and 1,384 test
artifacts**. All skill test records retain the original source-disjoint allocation.
There are 38 clipped code test inputs and 398 clipped skill test inputs; results
will distinguish those from complete input views. The small code test will need
wide uncertainty intervals and cannot establish small differences between models.

An initial integration check found that Python's `splitlines()` can split literal
Unicode separators inside JSON strings. The study reader now splits only ASCII
newlines. The original registration and correction are retained as an amendment;
data, policies and model requests are unchanged.

The code benchmark is a derived, grouped file-level subset of
[OMCBench](https://github.com/False-Positive-Community/open-malicious-code-benchmark).
The skill benchmark preserves the source-disjoint test population from
[MaliciousSkillBench](https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench).
The input budget is identical across families. These experiments do not test
whether a user's request to analyze a malicious artifact should be permitted.
