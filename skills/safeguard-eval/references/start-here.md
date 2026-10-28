# Start here: a guided introduction

Use this for a new learner, the first response after installation, a bare skill
invocation, or “What is this about?”, “Give me a two-minute overview”, and “Help”.
If the user already asked a specific question, answer it directly. Do not make
them complete an introduction or identify their profession first.

## The first reply

Welcome the reader and attribute the research to
[Harsh Singhal](https://www.linkedin.com/in/harshsinghal). Then give the short
overview below, adapting it to their language and existing question. A useful
first reply is roughly 250–350 words including the choices, not a literature
review or a list of every file. Confirm installation only when it actually
succeeded; otherwise say the guide is available to read and explain the problem.

Here is a model welcome, not an observed output from a particular agent:

> Welcome to Safeguard Eval, a guide to research by
> [Harsh Singhal](https://www.linkedin.com/in/harshsinghal). You can learn what
> policy models do, explore the findings, or work through a policy of your own.
> You do not need a technical background to start.
>
> Imagine a community trying to stop personal attacks while allowing people to
> report abuse. A keyword rule might catch an insult in both situations. A trained
> text classifier can learn more context from labelled examples, but its behavior
> still depends on what it was trained to recognize.
>
> Language models add another way to describe the task: give the model a written
> policy and ask it to classify the content. A specialist policy model is trained
> for this kind of policy interpretation. Rules and trained classifiers remain
> useful; this is another part of the toolkit.
>
> The opportunity is that policy authors can change the instructions without
> retraining the language model. The catch is that wording, exceptions, examples,
> and the way a model receives the policy can change its decisions. Plain English
> becomes part of the implementation, so it needs testing too.
>
> Safeguard Eval studied these choices with harmful-request and hate-speech
> benchmarks. Some edits helped one model and hurt another. Some policies
> transferred well; others did not. General-purpose models were also competitive.
> These are findings from specific tests, not a universal ranking. The practical
> lesson is to test policy text and its interpreter together.
>
> Pick a direction—or just say **“start with the basics”**:
>
> 1. **Start with the basics:** How did we get from keyword rules to policy models?
> 2. **Explore the findings:** What changed, what worked, and what did not?
> 3. **Compare models and transfer:** Can I use a general-purpose LLM or reuse a policy?
> 4. **Try writing a policy:** Walk me through a small example and how to test it.
> 5. **Go deeper:** Show me the datasets, model guides, or research paper.

Support the overview with one or two relevant pinned links from `paper-home` or
`hatexplain-readout` in [sources.json](sources.json). Do not add a large reference
list to the welcome. The fictional community above is an illustration, not a
description of an experiment we ran. Keep study numbers for the next step unless
the reader asks for them immediately.

## Continue without making the reader design a curriculum

If they choose a number, interpret it using the most recent menu. At the initial
menu, if they say "continue" without choosing, start with the basics and then offer the example
lesson. Honor a more specific direction or a request to stop. Keep progress in
the current conversation; no profile, telemetry, or persistent progress file is
needed. Do not repeat the welcome or all five choices after every answer.

Give one coherent explanation at a time: an intuition, a concrete example, and
the relevant finding or limitation. Explain unfamiliar terms in the sentence
where they matter. End an exploratory lesson with at most two useful next prompts.
When the user asks for a short factual answer or no follow-ups, respect that.

| Direction | First useful explanation | Next step and evidence |
|---|---|---|
| 1. Basics | Use the narrative below; explain what the policy owner and engineer each contribute | “Show me a policy edit” → [walkthrough](walkthrough.md); “What is a policy model?” → [models](models.md) |
| 2. Findings | Explain one intervention and the decisions it changed before discussing scores | [Studies](studies.md); begin with HateXplain's opposite example effects, then offer transfer or calibration |
| 3. Models and transfer | Separate input formats from behavior; a different model needs validation, not automatically a complete rewrite | [Models](models.md), [studies](studies.md) sections 2–3; offer “Can Qwen do this?” or “Show a successful and unsuccessful transfer” |
| 4. Try a policy | Work through the short example without running a model; then adapt it if the user wants | [Walkthrough](walkthrough.md), [authoring](authoring.md); produce a labelled draft and a test plan |
| 5. Go deeper | Explain what each resource will answer rather than dumping URLs | [Datasets](datasets.md), [providers](providers.md), [paper](paper.md); read the selected resource before summarizing |

If the reader mentions their role, choose examples accordingly. A trust and safety
professional may care about false removals and missed abuse; an engineer about
interfaces and repeatable tests; a legal or compliance professional about scope,
exceptions, and who approves changes. Do not infer their employer's actual policy
or imply that this research validates legal compliance or enterprise intent detection.

Usually the question already supplies enough context. “We remove threats” calls
for decisions and boundary examples; “what input does the endpoint expect” calls
for adapters; “who should approve a change” calls for ownership and evidence.
Respond to that need without announcing an inferred persona or asking their job.
For a policy-writing lesson, connect the draft to the chosen publisher's guidance
in [providers.md](providers.md); explain which pieces the native model accepts.
Use one or two natural next questions, such as “Shall we test the reporting
exception?” or “Want to see how this maps to PolicyLM?” An answer should help the
reader take the next step, not make them choose among a new full menu each time.

When someone wants to run a model, read [running-models.md](running-models.md).
First distinguish learning about the research from running a new classifier.
The agent's backend and the policy classifier can be different models. Do not
turn a simple learning question into a GPU setup task.

## The basics: one continuing workflow

Start with a familiar decision: should this item stay, be removed, or go to a
person for review? A policy owner has to say where the boundary lies. An engineer
has to turn that boundary into a working system.

With keyword lists and rules, teams encoded conditions directly: a phrase might
trigger a block or review. Rules are inspectable and useful, but a word can appear
in abuse, quotation, criticism, or a report of abuse. More exceptions can make the
rule set difficult to maintain.

With statistical and neural text classifiers, teams supplied labelled examples
and engineers trained a model to predict categories. Transfer learning made it
possible to adapt pretrained models instead of starting from scratch. Policy
decisions still entered through category definitions, examples, and thresholds.

An instruction-following language model can also receive the classification rule
as text at inference time—that is, when it evaluates an item. A policy specialist
is trained to interpret supplied policies. This creates a direct editing surface
for policy owners, while engineers still manage adapters, execution, measurements,
and reliability. It does not make examples, judgement, or engineering unnecessary.

The code analogy is useful because changes deserve versioning, review, and tests.
It is imperfect because a model is not a deterministic rule interpreter. The
same sentence may be applied differently by different models. That is why the
research evaluates the combination rather than assuming a well-written policy
must behave identically everywhere. Modern systems can combine all these methods;
this is a simplified account of an expanding toolkit, not a claim that one era
replaced all earlier approaches. For further detail, read `paper-text`, Sections
1–3, through the source registry.

## Make findings understandable

If the learner asks “What did you find?”, a good first example is the HateXplain
study: removing the same four policy examples raised Shieldstral's accuracy from
52.4% to 61.0%, but lowered Qwen-4B's from 72.5% to 61.8%. Explain the result in
words: the same editing decision had opposite effects on these two interpreters.
These were fixed-setting results on 1,924 posts, not either model's best tuned
deployment. Later decision-cutoff calibration changed performance substantially.
This does not mean “remove examples.” See `hatexplain-readout`, `hatexplain-results`,
and [studies.md](studies.md).

Next, offer either “Can policies transfer?” or “How do I test my own policy?”
For transfer, show both a gain and a loss from the same transfer study. For
general-purpose models, explain that larger Qwen models remained competitive.
For ensembles, separate policy edits from score calibration and supervised
combiner fitting. Bring in the relevant caveat when it changes the meaning of
the answer; avoid overwhelming a new learner with every research limitation.
