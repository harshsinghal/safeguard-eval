# Onboarding and guided learning

The skill should give a new learner a useful first answer, not just a successful
installation message. Its audience includes trust and safety, engineering, legal,
compliance, and people learning the subject without a technical background.

## The intended first experience

After successful installation through the shared prompt, the installing agent
reads `SKILL.md` and `references/start-here.md` and replies with:

1. A brief welcome crediting [Harsh Singhal](https://www.linkedin.com/in/harshsinghal).
2. A short narrative from keyword rules to trained text classifiers to policies
   supplied to language models. These methods can coexist.
3. The research question and practical finding, with limited detail at first.
4. Five learning directions and an easy default: “start with the basics.”

The five directions cover foundations, findings, model comparison and transfer,
trying a policy, and deeper resources. The next reply develops the selected idea
and offers at most two related prompts. A specific question skips the welcome.
The agent should not ask for the reader's role before providing value.

## How the handoff works

There is no install-time agent-execution hook in this package. The portable
mechanism is an explicit request in the installation prompt: after files are
installed, read the guide and deliver the welcome in the same response. The agent
can read those files directly even if its skill picker has not refreshed.

The Codex UI default prompt also asks for the two-minute introduction. The terminal
installer returns a `quick_start` object with the installed guide path and an
agent-specific starter prompt. Stdout remains valid JSON for existing consumers;
stderr adds the human-readable next step. Failed installation emits no success
result or welcome. A manual file copy requires invocation by the user or agent;
the package cannot guarantee that an arbitrary host immediately starts a chat.

The [official Codex documentation](https://developers.openai.com/codex/skills) and
[Claude Code documentation](https://code.claude.com/docs/en/skills) describe explicit
and implicit invocation. This design uses those conventions without changing
global agent settings, adding hooks, or launching another model process.

## Review the learning flow

These are acceptance scenarios for editorial or future behavioral review, not
claims that a live Codex/Claude Code session has already produced each answer.

| Input or situation | Expected behavior |
|---|---|
| Successful install using the shared prompt | Welcome and short overview immediately, with author link and five choices |
| Bare invocation or “What is this skill about?” | Same accessible starting point, without asserting a new installation occurred |
| “Start with the basics” | One continuing moderation workflow, explain terms, then offer a concrete edit |
| “2” after the initial menu | Develop a research finding with its task/configuration and relevant caveat |
| “Continue” after a lesson | Continue the current path; do not reset to the welcome |
| “Can policies transfer?” | Answer directly with success and failure; no universal prohibition |
| “Can I use a general-purpose LLM?” | Explain the Qwen comparison and scope, not a claim that specialists always win |
| “Try writing a policy” | Use the fictional walkthrough or supplied task; label the draft and cases as untested |
| “I'm in compliance; what does this mean for me?” | Emphasize scope, exceptions, review, and accountability; no implied legal certification |
| “Give me the numbers / paper” | Follow the selected evidence route; actually read the paper before claiming to summarize it |
| “Just answer this question; no tour” | Honor that preference; no forced curriculum or repeated menu |
| Installation fails | Report the problem and how to proceed; no false success message |

Keep fictional examples separate from study data. Do not turn the four walkthrough
cases into a benchmark score. Do not run paid inference or collect confidential
records to teach the exercise. Conversation context is sufficient for navigation;
no user profile, tracking, or persistent progress file is created.

## Verification for this release

The package tests exercise the installer handoff for both target agents, check
that the guide exists at the returned installed path, preserve JSON output, and
reject a package missing the guide. Existing update/backup and deterministic ZIP
checks still apply. The official skill validator checks the skill format.

These checks validate files and installation behavior. They do not guarantee that
every agent version follows every teaching instruction. A future live evaluation
should record the runtime, actual prompts and answers, and judged failures without
conflating authored welcome text with observed agent output.
