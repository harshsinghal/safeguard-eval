# Cyberattack requests and agent skill packages

Two registered studies extend our moderation comparisons to cyber assistance and
agent skill screening. Results are pending; no ranking is claimed yet.

- **Cyber requests:** distinguish attack-assistance requests from benign requests
  that change system state. This adapts CyberSecEval MITRE and FRR into a binary
  classification task; it is not Meta's native generation/refusal benchmark.
- **Skill packages:** screen complete textual packages from MalSkillBench, then
  compare with SKILL.md alone on the same test cases. No skill is installed or run.

PolicyLM, Shieldstral, Qwen, Kev, Clef and Jev are joined by Llama Guard 4. Prompt
Guard 2 is included only as an injection-detection diagnostic. Frozen Jina code
embeddings with fitted logistic and neural heads provide task-specific controls.

Each model gets three prespecified policy candidates. Validation selects the
policy; test inputs are released only after the selection is frozen publicly.
We report false blocks and missed harmful cases alongside balanced accuracy.

The group-separated test sets contain 332 cyber requests and 512 skill packages,
each evenly divided between ALLOW and BLOCK. The skill test contains 251 generated,
three wild and two tool-test malicious packages. Large and binary packages are
excluded. Results will describe this bounded cohort, not all wild agent skills.

See the [registered plan](PLAN.md) and [run instructions](RUNNING.md).
