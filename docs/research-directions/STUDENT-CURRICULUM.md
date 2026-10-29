# From Rules to AI: How Organizations Turn Policy into Practice

Recorded 29 October 2026 at Harsh Singhal's request. Parked for later development.
These are proposed articles, not completed lessons or a launched course. Recording
the outline does not schedule writing or change the released skill.

## Purpose and audience

An eight-week reading series for students from business, law, public policy,
computer science, and related disciplines. No programming or machine-learning
prerequisite. Introduce governance of AI-enabled content and enterprise systems
through the people, decisions, data, and controls involved.

Central lesson: a governance outcome reflects several people's work. Someone
defines the boundary, someone translates it into instructions, someone builds the
system, and someone checks whether it works. Policy authoring and AI engineering
are deeply coupled, within a wider process of accountability and operation.

Each week: one original, accessible article (roughly 1,000–1,500 words), one
optional existing companion reading, and a short discussion or exercise. Target
30–45 minutes of reading, as a design goal rather than a measured reading time.
Use plain language, introduce terms when needed, and carry one case through the
series instead of assembling disconnected technical primers.

## Continuing case

A fictional company operates a professional community where people discuss work
and careers. It must distinguish criticism from harassment, protect private
information, and handle complaints. Later it introduces an internal AI assistant.
Keep consumer moderation and enterprise governance distinct while showing the
shared need for policy, evidence, controls, and ownership. Use mild fictional
examples for exercises; raw harmful benchmark material is not required.

## Article sequence

### Week 1 — Who decides what an AI system should allow?

Start with the tension between free discussion and protection from abuse. Explain
why “keep the community safe” does not define an operational boundary. Introduce
product, Trust and Safety, legal, privacy/security, engineering, operations, and
affected users. Explain governance, risk, and compliance (GRC), and distinguish a
legal requirement, company policy, technical control, and evidence of performance.

Exercise: map who proposes, approves, implements, and reviews a harassment policy.
Companion: the overview of the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework),
as voluntary guidance rather than a compliance certificate.

### Week 2 — What happens after someone presses “Report”?

Follow detection, assessment, action, notification, appeal, and policy revision.
Explain keywords and rules, task-specific NLP classifiers, and language-model
policy evaluation as tools that can coexist. A keyword can catch an insult and
also someone quoting the insult to report it. Separate identifying a violation
from deciding an enforcement action; a model label does not itself mandate a ban.

Exercise: draw the workflow and identify where context and human judgment matter.
Companion: [Reddit's moderation, enforcement, and appeals explainer](https://support.reddithelp.com/hc/en-us/articles/23511059871252-Content-Moderation-Enforcement-and-Appeals).
Treat it as one platform's account, not a universal industry process.

### Week 3 — What does a language model do with your instructions?

Introduce tokens, training, inference, context, prompts, and fine-tuning through
classifying a community comment. Distinguish instructions, examples, and content
being assessed; distinguish a model from the application around it. Explain
general-purpose and specialist policy models without implying identical
architectures. Prompt changes alter inputs; fine-tuning alters weights. Fluent
answers and valid output formats do not guarantee correct decisions.

Exercise: identify instruction, policy, example, and assessed content in a request.
Companion: selected introductory sections of Google's
[What is a large language model?](https://developers.google.com/machine-learning/crash-course/llm/transformers).
Attention mathematics is optional.

### Week 4 — Before the model can be right, what does “right” mean?

Two reviewers disagree about criticism versus harassment. Introduce labeling
guides, units of analysis, contextual information, cultural/language differences,
adjudication, unresolved ambiguity, data provenance, and reviewer wellbeing.
Dataset labels record judgments under particular instructions; they are not
automatically an organization's desired policy. Do not treat majority voting as
proof that dissenting interpretations are wrong.

Exercise: independently label ten mild fictional comments, compare disagreements,
and revise the labeling guide. Companion: Google's
[Datasets: Labels](https://developers.google.com/machine-learning/crash-course/overfitting/labels),
especially the human-generated labels discussion.

### Week 5 — Writing a policy a model can apply

Turn “block harassment” into scope, definitions, prohibited behavior, permitted
cases, exceptions, examples, and expected outputs. Show edits such as a quotation
exception, a clearer targeting criterion, and a boundary example. Check that an
edit preserves intent. Explain model-specific templates/fields and adapters.
Use the code analogy for versioning, review, and testing, while recognizing that
model interpretation is less predictable than conventional program execution.

Exercise: write a one-page policy and six boundary cases. Companion: policy-writing
sections of the [GPT-OSS Safeguard user guide](https://developers.openai.com/cookbook/articles/gpt-oss-safeguard-guide),
as provider-specific guidance, not a universal optimum.

### Week 6 — How do you know a policy change helped?

Explain training/validation/test separation, leakage, controlled comparisons,
false blocks, missed violations, precision, recall, and F1 with small counts
before formulas. Ask whose experience changes when the aggregate score improves.
Introduce Safeguard Eval only after these foundations: policy edits, structure,
examples, native adapters, and transfer that can help or hurt. Benchmarks are
worked examples with limitations, not universal model rankings. Calibration and
ensembles can be optional extensions, clearly distinct from editing policy text.

Exercise: compare two prepared result tables and recommend a revision with stated
trade-offs. Companion: [the HateXplain readout](../hatexplain/READOUT.md),
“The same policy edit can help one model and hurt another.”

### Week 7 — From community moderation to enterprise AI

Follow an internal assistant from user prompt through retrieval, response, and
possible action. Distinguish acceptable use, document permissions, output checks,
and action authorization. An intent classifier cannot repair source permissions
or reliably expose hidden intentions. Introduce API/self-hosted deployment,
privacy, latency, cost, vendor review, logging, and responsibility boundaries.

Exercise: diagram the data flow and name the team responsible for each control.
Companion: selected [GitLab Glean handbook](https://handbook.gitlab.com/handbook/eta/ai/tools/glean/)
sections on reviewing connectors and agent capabilities. This is an operational
example, not a provider endorsement.

### Week 8 — The system is live. Who owns its mistakes?

Investigate mistaken removals after a policy update. Cover monitoring, appeals,
human review capacity, policy/model versions, regression tests, shadow rollout,
rollback, incident handling, and helping affected people. Governance continues
after deployment; new traffic and changed models can invalidate earlier evidence.

Exercise: role-play a launch review with policy, engineering, legal, operations,
and user perspectives; recommend launch, revision, or delay. Companion: “Notice”
and “Appeal” in the [Santa Clara Principles](https://www.santaclaraprinciples.org/),
as civil-society guidance rather than binding law.

## Student portfolio and use of the skill

Build a stakeholder map, workflow, labeling guide, policy, evaluation plan, and
operating plan incrementally. Assess reasoning, preservation of policy intent,
trade-offs, and evidence quality rather than the highest benchmark score. The core
course uses prepared examples and results; no GPU rental or paid API is required.

The skill can explain cited passages, ask comprehension questions, walk through
fictional examples, and identify missing evidence. Suggested prompts:

- Explain this using the fictional company from this week's article.
- Ask three questions to check my understanding.
- Which statements are measured findings, and which are recommendations?
- What evidence is missing from my proposed policy change?

Reviewed articles and instructor notes anchor factual answers. Agent responses
remain checkable against them; the skill is not an error-free instructor. A
reviewed answer key and tested student mode remain future work, not delivered
features. Refresh external links and provider guidance before publishing lessons.

## Six-week option

Combine weeks 1–2 into one edited article and weeks 7–8 into another. Keep one
companion per merged week rather than doubling the reading load.

Next step when resumed: review the arc, write the first article and instructor
notes, test comprehension with students, then use that feedback to shape the rest.
