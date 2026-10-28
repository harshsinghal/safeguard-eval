# Test the installed skill as a user

This is a usability test of an installed skill in Pi with a lower-cost model.
It is separate from the moderation benchmarks. The question is whether an ordinary
question leads to an accurate, understandable answer and a useful conversation.

## Plan and progress

- [x] Inspect Pi's installed documentation and native session format (0.87.1).
- [x] Verify OpenRouter's exact model ID: `openai/gpt-6-luna`.
- [x] Install a complete skill into a separate Pi profile; preserve existing defaults.
- [x] Record prompts, answers, tool use, model identity, usage, and feedback locally.
- [x] Try realistic, multi-turn conversations without extra answer instructions.
- [x] Inspect failures and make narrow improvements to the skill.
- [x] Test a small local Ollama classification example; record its limits separately.

The [evidence note](evidence/2026-10-28/README.md) records the findings. Package
validation and publication are recorded separately in the release notes so this
evidence record can remain immutable. Future human feedback is still to be collected.

## What the test must preserve

Use Pi's normal system prompt, normal tools, and ordinary skill discovery. Isolate
this skill from unrelated installed skills and extensions so the result is
attributable. Do not inject expected answers, preload all the reference files, or
silently substitute a stronger model. The feedback extension adds no model-facing
instructions. A direct `/skill:safeguard-eval` invocation is a separate test from
an ordinary question that requires the model to discover the skill.

Record the skill version and a snapshot of the files for every session. Record
the exact model, thinking setting, runtime version, tool configuration, prompts,
responses, errors, and whether the model read the relevant sources. An installed
folder passing validation does not establish that an inexpensive model uses it well.

## Run the lab

From a checkout of this repository, with Python 3.10+ and Pi installed:

```bash
python3 tools/pi_skill_lab.py setup --key-file /path/to/OPENROUTER_API.txt
python3 tools/pi_skill_lab.py start
```

The default lab is `~/workspace/safeguard-eval-feedback`. Its Pi profile, sessions,
skill snapshots, and review files are private local files outside the repository.
The key is read into the child process environment; it is not copied into model
configuration or passed as a command-line argument. The setup stores the key-file
path, not its value. The agent API still sends the conversation and any tool output
it uses to OpenRouter and its inference provider. Local logs do not mean local
inference or a zero-retention contract.

The normal interactive session starts without a scripted first question. Ask what
a new user would ask. `/skill:safeguard-eval` explicitly opens the skill if needed.
Use `/feedback Your note here` to attach a note to the last answer without sending
that note to the model. Use `/lab-usage` to see Pi's recorded usage. Exit normally;
the launcher writes a readable `review.md` and structured `review.json`.

```bash
# A later review; no model call or upload
python3 tools/pi_skill_lab.py report

# Controlled multi-turn smoke test; each line is one ordinary user question
python3 tools/pi_skill_lab.py start --questions /path/to/questions.json --label smoke
```

The questions file is a JSON array of strings. This mode resumes the same native
Pi session between questions and stops on errors; it does not insert an answer key.

The lab uses a modest request limit and an estimated cost stop as backstops, not a
provider billing guarantee. Pi's cost metadata can differ from the bill. A dedicated
OpenRouter key with a provider-side spending limit is the stronger control. The
tool does not change account-level limits. Every run reports usage even when it
fails. Do not paste credentials into the conversation.

The initial backstops are 100 model responses and $0.50 estimated cost per Pi
session. They act after recorded responses and can overshoot; they are not a hard
ceiling on the account. Starting another session resets these session backstops.
The lab disables idle cache warming and automatic retries. The exact defaults are
recorded in `lab.json` and each run's metadata.

## Review the experience, not just factual accuracy

Try a short conversation in each direction, without announcing a persona:

- “What is this about? I don't know the model names.” Then “Show me a simple example.”
- “We remove threats but want people to report abuse. Help me write that policy.”
  Then “Which cases should I test?”
- “Can I move a PolicyLM policy to Qwen unchanged?” Then “What has to stay fixed?”
- “Can this block employees looking for layoff information?” Then “What hasn't
  been tested?”
- “Can I run this locally?” Then “What would it cost to use a GPU provider?”

For each answer, note whether it answered the actual question, used the relevant
reference, preserved the limits of the evidence, explained unfamiliar terms,
and offered a sensible next step. Look for excess detail, repeated welcomes,
invented numbers, absolute transfer claims, and unverified hosting claims.
Keep unsuccessful answers. Label assistant-run smoke tests separately from the
author's later user sessions; neither is a blind or representative usability study.

## Bring feedback back

Tell the reviewing agent: “Review my latest Safeguard Eval Pi session in
`~/workspace/safeguard-eval-feedback`.” It can read the local review and, if needed,
the native session. Nothing is automatically sent back to the author or published.
The readable export excludes reasoning blocks and tool payloads, and masks common
credential patterns. It is not an anonymization guarantee. Review it before sharing;
raw sessions can contain file contents, personal information, or secrets.

The extension indexes sessions selected during the run, including new/forked
sessions. Reports group original visible turns by first-seen session file, retaining
branch IDs rather than blending alternative answers into one conversation. Copied
fork ancestors count once. Usage includes abandoned
branches and ancillary recorded work, since those requests can still be billed.
Resuming a historical session includes its prior recorded usage; it is not all
new spending in the current launch.
The export is a conversation review, not a reconstruction of every compacted or
edited context the model saw.
