# Can policy models recognize prompt injection without blocking ordinary text?

**Status: prepared; no new model results yet.** The six-model execution is awaiting the requested allocation of up to $8. Preparation has incurred **$0 in GPU/API charges**, and no GPU has been provisioned.

This follow-up compares **PolicyLM, Shieldstral, GPT-OSS Safeguard, Jev, Kev and Clef-Flash** on a different question from WildGuard harmfulness: does the submitted text try to override an AI's instructions or restrictions?

The benchmark will include both attack detection and false blocks. A prompt can contain strange symbols or discuss a jailbreak without itself being an attack. Conversely, an instruction override can use ordinary language.

| Test | Examples | What we will measure |
|---|---:|---|
| xTRam1 safe-guard-prompt-injection | 2,060 | Both attack recall and benign allow rate, plus balanced metrics |
| deepset prompt-injections | 116 | The same measures on a second published test split |
| NotInject | 339 | False blocks on legitimate text with suspicious wording |
| JailbreakBench GCG / PAIR artifacts | 182 | Detection of released attack attempts, including optimized suffixes |

There are **2,697 final examples**, kept in separate result tables. Eighteen PAIR records have no released attack prompt and are excluded. Published binary labels are retained, including their limitations: some source examples lack the governing context needed to tell a task change from an injection. The scores will describe annotation agreement, not a guarantee of security.

The preparation audit removed **336 training rows** that overlapped evaluation material under a fixed text-similarity rule. We reserved **256 fitting and 256 validation examples**, balanced by source and label. Model outputs have not yet been collected.

Each model will get three candidates: a brief policy; a more explicit policy with attack mechanisms and benign exceptions; and the explicit policy with four fitting examples that prioritize that model's mistakes. Validation selects the policy for each model. The final tests compare that selection with the brief baseline. **No score calibration, cutoff tuning, ensemble or weight update is included.** PolicyLM retains its publisher's fixed 0.335 precision preset; the other models use their stated categorical or argmax decisions.

The native adapters matter here. PolicyLM has rule fields and a standard text cleaner; Shieldstral uses an instruction/query/document wrapper; Kev, Clef and Jev use Choice interfaces; Safeguard reads a system policy. Those differences will be recorded alongside the results.

This does not test a live application's resistance to injection. It does not execute the attacks, or test retrieved documents, tool outputs, or multi-turn agents. PolicyLM's own card also excludes use as a sole adversarial security boundary.

- [Registered experiment design and limitations](PLAN.md)
- [Run and reproduce the study](RUNNING.md)
- [Implementation](../../evals/prompt_injection/)
- [Dataset audit](preparation/data-audit.json)
- [Pinned source manifest](preparation/source-manifest.json)
- [Earlier injection pilot with different decision rules](../../evals/injection/README.md)

The main WildGuard/HateXplain leaderboard remains unchanged. Injection results will form a separate comparison because the labels, populations and decision rules differ.
