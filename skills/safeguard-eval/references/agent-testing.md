# Test the experience in the user's own agent

The skill is portable instructions and references, not a separate agent or a
model upgrade. Codex, Claude Code, and Pi discover skills differently; their
backends can differ in whether they read files, follow caveats, cite correctly,
or continue a helpful conversation. A lower-cost model is worth testing rather
than assuming it will behave like a frontier model.

Start with an ordinary question: “What is Safeguard Eval about?” Follow naturally
into an example, a finding, or an implementation question. Avoid giving the model
an answer key or preloading every guide. Inspect whether it read the relevant
files, kept source and recipient models straight, and suggested useful next steps.
For an explicit invocation in Pi, use `/skill:safeguard-eval`. See the
[Pi skill documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md).

There are two different tests: a user asking a research question should receive
a grounded explanation; a user asking to run a classifier needs an explicit setup
and evaluation. Good performance at one does not establish the other.

## Optional conversation review

Pi stores native JSONL sessions with prompts, responses, model changes, and usage.
The repository's `pi-lab-guide`, `pi-lab-runner`, and `pi-feedback-extension` sources
provide an opt-in, isolated profile for testing the installed skill through
OpenRouter. Resolve those IDs through [sources.json](sources.json).
The extension adds a local `/feedback` command; it does not supply better answers
or extra policy instructions. Ordinary skill installation does not enable logging
beyond whatever the user's agent already does.

The lab writes local readable reviews and native logs. There is no automatic upload
to Harsh Singhal or the repository. Inference through a hosted backend still sends
the conversation and used tool output to that backend. Credentials must stay out
of prompts. Raw sessions can include tool outputs and private information; review
exports before sharing them. Automated masking is not a privacy guarantee.

When asked to analyze feedback, separate incorrect research claims, confusing
explanations, navigation failures, missing source access, and runtime failures.
Quote only the relevant visible exchange. Keep model identity, skill version, and
test conditions with the finding. Do not claim the problem is fixed from a file
edit alone; try the affected conversation again and retain the original failure.

Also try a new scenario that exercises the same skill: whether example decisions
follow a different rule, whether an unresolved review choice survives an edit,
whether the exact requested model pair is retrieved on the first answer, and
whether the learner can turn a finding into a small experiment. Keep expected
outcomes in the review notes, not in a hidden prompt to the tested agent. Normal
user corrections are part of the conversation; disclose when they were needed.
Separate policy-content errors from bad citations and poor teaching flow. A lookup
helper can protect numerical comparisons but cannot settle an ambiguous policy.

The project's v0.5 development checks (`skill-learning-readout` and
`skill-learning-runs` in [sources.json](sources.json)) retained failures as well as
retests. The lookup returned correct recorded numbers, but some explanations still
blurred selection roles, used an indirect citation, or broadened an unresolved
exception. These are known limits, not guarantees that another conversation will
repeat or avoid the same mistake. Review the draft's meaning with the owner and
keep new tests separate from the examples used to improve the skill.

Budgeted test calls should report usage and distinguish the agent's estimate from
provider billing. A local estimated stop is not a provider-side hard spending cap.
See [running-models.md](running-models.md) for neutral deployment and cost guidance.
