# Safeguard Eval skill

Ask your agent about policy models, policy writing, and what the Safeguard Eval
experiments actually found. The skill supplies a research guide and traceable
evidence; your existing agent answers the questions. It needs no API keys, GPU,
model downloads, or paid service to use its bundled guides.

**Version 0.1.0 · evidence through 28 October 2026 · Codex and Claude Code**

[Download the skill](https://github.com/harshsinghal/safeguard-eval/releases/tag/skill-v0.1.0)
or browse [all releases](https://github.com/harshsinghal/safeguard-eval/releases).
The release ZIP contains just the skill, not the full research repository.

## What you can ask

- “Why does policy writing need to be tested with a particular model?”
- “How do PolicyLM, Shieldstral, CoPE, and Safeguard accept policies?”
- “What changed in the HateXplain policies? Did examples always help?”
- “Show me a policy transfer that worked and one that failed.”
- “Did the ensembles beat individual models after calibration?”
- “Help me write an initial policy and design a small test for it.”

The skill explains the practical lesson without making a blanket claim that
policies cannot transfer. Some did. It distinguishes model formats, rule wording,
thresholds, and supervised ensemble fitting, and links to the evidence for each.

## Install by asking your agent

Paste this into **Codex or Claude Code**:

```text
Install the Safeguard Eval skill for this agent from the official release:
https://github.com/harshsinghal/safeguard-eval/releases/tag/skill-v0.1.0

Read its installation instructions:
https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.1.0/skills/safeguard-eval/README.md

Download the skill ZIP and SHA256SUMS, verify the ZIP checksum, inspect the
package, and install the whole safeguard-eval folder for my current agent.
Use the included Python installer for Codex or Claude Code. Preserve any
existing installation; do not overwrite local changes without a backup.
Do not install model weights, research dependencies, or run experiments.
Then use the skill to explain why policy transfer needs to be tested.
```

An agent needs network access and permission to write its skill directory to carry
out that installation. The checksum detects damaged or mismatched downloads; it
is not a separate publisher signature. Use the official repository as the source.

In **Codex**, the built-in skill installer is another option:

```text
Use $skill-installer to install the skill at
https://github.com/harshsinghal/safeguard-eval/tree/skill-v0.1.0/skills/safeguard-eval
```

That installer chooses the directory supported by your Codex installation. Some
versions use `~/.codex/skills`; the portable installer below uses the current
documented `~/.agents/skills` location. Avoid installing duplicate copies in both.

## Install from a terminal

Use Python 3.10 or later. On macOS or Linux, run these commands in an empty working
directory after reviewing the package source:

```bash
curl -fL https://github.com/harshsinghal/safeguard-eval/releases/download/skill-v0.1.0/safeguard-eval-skill-v0.1.0.zip -o safeguard-eval-skill-v0.1.0.zip
curl -fL https://github.com/harshsinghal/safeguard-eval/releases/download/skill-v0.1.0/SHA256SUMS -o SHA256SUMS
shasum -a 256 -c SHA256SUMS
unzip safeguard-eval-skill-v0.1.0.zip
```

Then choose your agent:

```bash
# Codex, available across projects
python3 safeguard-eval/scripts/install.py --target codex

# Claude Code, available across projects
python3 safeguard-eval/scripts/install.py --target claude-code
```

| Agent | Personal destination | Project destination |
|---|---|---|
| Codex | `~/.agents/skills/safeguard-eval` | `.agents/skills/safeguard-eval` |
| Claude Code | `~/.claude/skills/safeguard-eval` | `.claude/skills/safeguard-eval` |

For a project installation, add `--scope project --project /path/to/project`.
For a custom or older Codex location, supply the full path with, for example,
`--dest "$HOME/.codex/skills/safeguard-eval"`.
You can also copy the entire folder manually to a documented skill directory.
Keep `SKILL.md`, references, metadata, and supporting files together.

These paths follow the [Codex skills documentation](https://developers.openai.com/codex/skills)
and [Claude Code skills documentation](https://code.claude.com/docs/en/skills).
This package targets local Codex and Claude Code skill discovery; it does not
configure a cloud connector or a separate hosted agent.

## Use it

In Codex, select the skill or ask:

```text
Use $safeguard-eval to explain how I should write and test a policy for Shieldstral.
```

In Claude Code:

```text
/safeguard-eval Explain policy transfer using a successful and an unsuccessful example.
```

Both agents can also select it automatically for a matching question. If it does
not appear after installation, start a new session or restart the agent. When
offline, it can answer from the bundled snapshot and disclose that boundary.
Network access lets it inspect the full commit-pinned research files.

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

The [guide](SKILL.md) routes questions to four short references. The
[source registry](references/sources.json) pins the original files to a Git commit;
[numeric anchors](references/results.json) are generated from frozen result JSON.
[Release metadata](release.json) gives the evidence date. No benchmark prompts,
model weights, credentials, or executable research models are in this package.

CI checks source drift, new study directories, generated numbers, package integrity,
and installation behavior. It does **not** rewrite the prose or establish that an
agent will answer every question correctly. A maintainer reviews new findings,
updates the guides, and issues a new version. See the
[maintenance guide](https://github.com/harshsinghal/safeguard-eval/blob/skill-v0.1.0/docs/skill/MAINTAINING.md).

The skill package is [MIT licensed](LICENSE). Models, datasets, and linked material
outside the package keep their own terms. This is an independent research skill,
not an endorsement by the model or agent providers.
