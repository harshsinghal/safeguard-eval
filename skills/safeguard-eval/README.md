# Safeguard Eval skill

Ask your agent about policy models, datasets, policy writing, and what the
Safeguard Eval experiments actually found. The skill is a gateway to the research:
plain-language guides, measured findings, provider references, and the paper.
Your existing agent answers the questions. Reading the bundled guides needs no
additional GPU, classifier download, or service; your agent backend may still
have subscription or API charges.

Based on work by **[Harsh Singhal](https://www.linkedin.com/in/harshsinghal)**.

**Version 0.4.0 · evidence through 28 October 2026 · Codex, Claude Code, and Pi**

[Download the skill](https://github.com/harshsinghal/safeguard-eval/releases/tag/skill-v0.4.0)
or browse [all releases](https://github.com/harshsinghal/safeguard-eval/releases).
The release ZIP contains just the skill, not the full research repository.

## A place to start

You do not need to know the model names or research terminology. The installation
prompt below asks your agent to begin with a short welcome and a two-minute
overview, then offer five directions:

1. **Start with the basics:** From keyword rules and text classifiers to policy models.
2. **Explore the findings:** What we changed, what helped, and what did not.
3. **Compare models and transfer:** General-purpose LLMs, specialist models, and reusing policies.
4. **Try writing a policy:** A small example, boundary cases, and a test plan.
5. **Go deeper:** Datasets, official model guides, and the research paper.

You can reply with a number, a question, or simply **“start with the basics.”**
The agent should explain one idea at a time and suggest relevant follow-ups. It
can tailor examples to trust and safety, engineering, or compliance work without
requiring you to choose a role first.

Preview the [guided introduction](references/start-here.md) or the
[hands-on how-to](references/walkthrough.md). The exercise is a teaching example;
it does not run or deploy a model.

## What you can ask

- “Why does policy writing need to be tested with a particular model?”
- “What are WildGuardMix and HateXplain, and what did you test from each?”
- “How do PolicyLM, Shieldstral, CoPE, and Safeguard accept policies?”
- “Find their official model cards and policy-authoring guidance.”
- “What changed in the HateXplain policies? Did examples always help?”
- “Show me a policy transfer that worked and one that failed.”
- “Did the ensembles beat individual models after calibration?”
- “Help me write an initial policy and design a small test for it.”
- “Read the research paper and explain the findings for a trust and safety team.”
- “Which ROOST resources should I explore for a model you haven't tested?”

The skill explains the practical lesson without making a blanket claim that
policies cannot transfer. Some did. It distinguishes model formats, rule wording,
thresholds, and supervised ensemble fitting, and links to the evidence for each.
Its search guide directs unanswered questions to primary sources and distinguishes
provider recommendations from results we measured. Untested models and proposed
applications are labelled explicitly.

## Explore the reference library

| Start here | What it explains |
|---|---|
| [Welcome and learning paths](references/start-here.md) | A short introduction, moderation's evolving toolkit, and where to go next |
| [Hands-on how-to](references/walkthrough.md) | From a policy intention to a draft, example decisions, and a test plan |
| [Datasets](references/datasets.md) | Sources, labels, splits, exclusions, and the difference between benchmarks and demos |
| [Model interfaces](references/models.md) | How the tested adapters delivered policies and read decisions |
| [Provider reading guide](references/providers.md) | Weight downloads, OpenAI/ROOST authoring guidance, other providers, and untested discoveries |
| [Studies and findings](references/studies.md) | What changed, the numbers, unsuccessful results, and limitations |
| [Authoring and testing](references/authoring.md) | How to draft a policy and test it with the intended model |
| [Running models](references/running-models.md) | Local testing, hosted inference, rented GPUs, neutral provider guidance, usage and teardown |
| [Testing the agent experience](references/agent-testing.md) | Cheap backends, normal conversations, and opt-in local feedback |
| [Paper guide](references/paper.md) | How an agent can retrieve, read, and cite the consolidated draft |
| [Search guide](references/search.md) | Where to look when the project cannot answer the question |

The [research paper](https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.4.0/research-preprint/README.md)
is available as a PDF, extracted text, and LaTeX source package. It is author
review draft v0.5, **not peer reviewed or submitted to arXiv**. The paper is fetched
on demand rather than included in the small skill ZIP.

## Install by asking your agent

Paste this into **Codex, Claude Code, or Pi**:

```text
Install the Safeguard Eval skill for this agent from the official release:
https://github.com/harshsinghal/safeguard-eval/releases/tag/skill-v0.4.0

Read its installation instructions:
https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.4.0/skills/safeguard-eval/README.md

Download the skill ZIP and SHA256SUMS, verify the ZIP checksum, inspect the
package, and install the whole safeguard-eval folder for my current agent.
Use the included Python installer for Codex, Claude Code, or Pi. Preserve any
existing installation; do not overwrite local changes without a backup.
Do not install model weights, research dependencies, or run experiments.

After installation succeeds, read the installed SKILL.md and
references/start-here.md. In your first reply after installation, welcome me,
credit Harsh Singhal with his LinkedIn link, give the short introduction, and
offer the five learning paths. Do not stop at "installed" or ask me to decide
what to learn before giving the overview. If the skill has not appeared in your
picker yet, read those installed files directly to give the welcome now.
```

An agent needs network access and permission to write its skill directory to carry
out that installation. The checksum detects damaged or mismatched downloads; it
is not a separate publisher signature. Use the official repository as the source.

In **Codex**, the built-in skill installer is another option:

```text
Use $skill-installer to install the skill at
https://github.com/harshsinghal/safeguard-eval/tree/skill-v0.4.0/skills/safeguard-eval
Then read its SKILL.md and references/start-here.md and give me the welcome,
two-minute overview, and suggested learning paths in the same reply.
```

That installer chooses the directory supported by your Codex installation. Some
versions use `~/.codex/skills`; the portable installer below uses the current
documented `~/.agents/skills` location. Avoid installing duplicate copies in both.

## Install from a terminal

Use Python 3.10 or later. On macOS or Linux, run these commands in an empty working
directory after reviewing the package source:

```bash
curl -fL https://github.com/harshsinghal/safeguard-eval/releases/download/skill-v0.4.0/safeguard-eval-skill-v0.4.0.zip -o safeguard-eval-skill-v0.4.0.zip
curl -fL https://github.com/harshsinghal/safeguard-eval/releases/download/skill-v0.4.0/SHA256SUMS -o SHA256SUMS
shasum -a 256 -c SHA256SUMS
unzip safeguard-eval-skill-v0.4.0.zip
```

Then choose your agent:

```bash
# Codex, available across projects
python3 safeguard-eval/scripts/install.py --target codex

# Claude Code, available across projects
python3 safeguard-eval/scripts/install.py --target claude-code

# Pi, available across projects
python3 safeguard-eval/scripts/install.py --target pi
```

| Agent | Personal destination | Project destination |
|---|---|---|
| Codex | `~/.agents/skills/safeguard-eval` | `.agents/skills/safeguard-eval` |
| Claude Code | `~/.claude/skills/safeguard-eval` | `.claude/skills/safeguard-eval` |
| Pi | `~/.pi/agent/skills/safeguard-eval` | `.pi/skills/safeguard-eval` |

For a project installation, add `--scope project --project /path/to/project`.
For a custom or older Codex location, supply the full path with, for example,
`--dest "$HOME/.codex/skills/safeguard-eval"`.
You can also copy the entire folder manually to a documented skill directory.
Keep `SKILL.md`, references, metadata, and supporting files together.
Pi's personal destination honors `PI_CODING_AGENT_DIR` when set. Pi also discovers
the shared `.agents/skills` locations; avoid installing duplicate copies.

The terminal installer prints a starter prompt for your selected agent and the
quick-start file path. Paste that prompt into your agent to begin the guided tour.

These paths follow the [Codex skills documentation](https://developers.openai.com/codex/skills)
and [Claude Code skills documentation](https://code.claude.com/docs/en/skills), and
the [Pi documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md).
This package targets local skill discovery; it does not
configure a cloud connector or a separate hosted agent.

## Use it

In Codex, select the skill or ask:

```text
Use $safeguard-eval to give me a two-minute introduction and suggest what to explore next.
```

In Claude Code:

```text
/safeguard-eval Give me a two-minute introduction and suggest what to explore next.
```

In Pi:

```text
/skill:safeguard-eval Give me a two-minute introduction and suggest what to explore next.
```

These agents can also select it automatically for a matching question. If it does
not appear after installation, start a new session or restart the agent. When
offline, it can answer from the bundled snapshot and disclose that boundary.
Network access lets it inspect the full commit-pinned research files.

You can skip the tour and ask a specific question at any time. The welcome should
not repeat on every answer. The shared installation prompt requests an immediate
introduction; a manual file copy alone does not start a conversation in your agent.

## Try it with an inexpensive agent backend

Ask natural questions and follow the answers: “What is this about?”, “Show me an
example”, “Would that policy work with another model?”, or “How can I run it?”
The agent should adapt to the question without asking you to pick a profession.
Skill portability does not guarantee equal answers from every model or harness.

The optional [Pi user-test lab](https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.4.0/docs/skill/PI-USER-TEST.md)
uses an isolated Pi profile with OpenRouter's `openai/gpt-6-luna`. It records native
sessions, readable local reviews, model identity, token usage, and cost information.
Use `/feedback` in that lab to mark an answer. The extension adds no answer
instructions. Installing the skill alone does not enable the lab or upload logs.
Hosted inference still sends the conversation to the chosen backend.

Other harnesses can read the same `SKILL.md` and relative reference files through
their documented skill support. No behavioral guarantee is implied for untested
harnesses. The [agent-testing guide](references/agent-testing.md) explains what to
check, and the [running guide](references/running-models.md) distinguishes the
agent backend from the policy classifier you may later want to run.

## Update or remove it

Download a newer release from the same repository and verify its checksum. Run
that release's installer with `--update` and the same target, scope, and destination
options you used initially. For example, from the extracted newer package:

```bash
python3 safeguard-eval/scripts/install.py --target codex --update
```

Updates preserve the old directory, including local edits, in `skill-backups`
beside the `skills` directory. The installer prints the exact backup path. An
identical install is a no-op; an unrelated directory or symbolic-link destination
is not replaced. Review and port any local changes yourself. There are no background
updates, scheduled jobs, telemetry, or changes to global agent instructions.

To remove it, delete only the installed `safeguard-eval` directory for that agent.
Backups remain until you choose to remove them. For a symlink installation managed
elsewhere, remove the symlink rather than its source directory.

## Evidence and maintenance

The [guide](SKILL.md) routes questions to focused references. The
[source registry](references/sources.json) pins the original files to a Git commit;
[numeric anchors](references/results.json) are generated from frozen result JSON.
[Release metadata](release.json) gives the evidence date. No benchmark prompts,
model weights, credentials, or executable research models are in this package.
The [external catalog](references/external-sources.json) records primary-source
links and whether each relates to a tested checkpoint, used dataset, provider
guidance, or untested discovery. Those live pages can change after the check date.

CI checks source drift, new study directories, generated numbers, package integrity,
and installation behavior. It does **not** rewrite the prose or establish that an
agent will answer every question correctly. A maintainer reviews new findings,
updates the guides, and issues a new version. See the
[maintenance guide](https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.4.0/docs/skill/MAINTAINING.md).

The skill package is [MIT licensed](LICENSE). Models, datasets, and linked material
outside the package keep their own terms. This is an independent research skill,
not an endorsement by the model or agent providers.
