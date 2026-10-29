# Findings to carry into the next round of writing

Recorded 29 October 2026. This is an editorial handoff for the research paper,
magazine article, media article, and learning skill. It adds no experiment and
does not change the frozen leaderboard. The current papers have not yet been
revised to include this handoff.

## The message the evidence supports

Policy authoring is deeply coupled with AI engineering. The evaluated system is
the policy text, the model interpreting it, its input adapter, and the rule that
turns its score into an action. Changing the objective used to select that system
can change which configuration wins and which people experience its mistakes.

Our results support evaluating policy adaptation and lightweight ensembles before
assuming that a new language-model fine-tune is required. They do not establish
that fine-tuning is unnecessary or that one model family is generally superior.
The released models were themselves trained; our experiments left their language-
model weights unchanged. Learned calibrators and ensemble combiners did use
labeled fitting data.

## Evidence that is already preserved

- [Interactive leaderboard](../../published_runs/2026-10-29-leaderboard/index.html):
  offline HTML with both benchmarks, three objectives, coverage, and paired
  comparisons. GitHub readers must download the HTML to open it.
- [Readable findings](README.md), [complete tables](../../published_runs/2026-10-29-leaderboard/RESULTS.md),
  and [CSV](../../published_runs/2026-10-29-leaderboard/leaderboard.csv).
- [Evidence bundle](../../published_runs/2026-10-29-leaderboard/README.md):
  frozen choices, exact policies/configurations, normalized prompt-free outputs,
  input hashes, archived source, and reproduction instructions.
- [Original Jev study](../jev/READOUT.md) and
  [policy changes](../jev/POLICY-CHANGES.md): preserve the original
  accuracy-oriented analysis alongside the newer balanced selection.
- [Jev and local decision models](../research-directions/JEV-AND-LOCAL-DECISION-MODELS.md):
  a separate literature review and proposal. Its proposed experiments are not results.

The leaderboard's implementation and evidence were committed in `0627356` on
`codex/jev-benchmark`. At the time of this handoff these branch changes are local;
the `published_runs` directory name does not mean that they have been pushed to
GitHub or deployed publicly.

## Claim ledger

### F1. Balanced performance depends on the task

On WildGuardTest, the equal log-odds specialist ensemble had the highest observed
balanced accuracy, **91.08%**. The best individual configuration was CoPE at
**90.58%**. Qwen3.5 27B scored **90.16%**, WildGuard **89.81%**, and Jev **88.69%**.

On HateXplain, the specialist-plus-Qwen log-odds logistic ensemble scored **79.35%**.
Jev was the highest-scoring individual at **78.40%**, followed by Shieldstral
**77.02%**, Qwen3.5 4B **76.21%**, and PolicyLM **63.69%**. Only these four
individual models had full HateXplain tests; the other WildGuard models were
not evaluated there.

Use this to explain why a model should be assessed against the intended policy
and content. Do not write that Jev beats policy models in general, or that small
specialists always beat general-purpose models.

### F2. Close ranks are not settled differences

The leading WildGuard ensemble's advantage over CoPE was **0.50 percentage
points**, paired 95% interval **−0.07 to +1.11**. On HateXplain, the leading
ensemble's advantage over Jev was **0.95 points**, interval **−1.03 to +2.94**.
Jev's advantage over Shieldstral was **1.38 points**, interval **−0.66 to +3.49**.

These are unadjusted, descriptive paired bootstrap intervals conditional on
stored predictions. They do not account for the full model/policy search, prior
test inspection, or uncertainty in historical training exposure.

### F3. Lightweight combinations can be useful

The leading WildGuard ensemble exceeded the released WildGuard model by **1.27
balanced-accuracy points**, interval **+0.33 to +2.21**. It missed **93** violations
versus **113**, while falsely blocking **52** compliant prompts versus **51**.

The leading HateXplain ensemble exceeded Shieldstral by **2.33 points**, interval
**+0.94 to +3.79**. It did not establish a clear advantage over Jev. The ensembles
did not include Jev.

This supports a practical alternative worth testing. It is not a controlled
comparison of equally resourced fine-tuning and ensembling, and it does not show
that running several models is operationally cheaper than running one.

### F4. The metric changes the workflow

The original accuracy-oriented Jev configuration on HateXplain used the policy
with four fitting examples and a 0.90 BLOCK cutoff. It achieved **80.67% accuracy**,
**74.93% balanced accuracy**, and **59.93% hate recall**, with **134 false blocks**
and **238 missed hate posts**.

The newer balanced selection chose the detailed policy without those examples
and a 0.75 cutoff. It achieved **78.12% accuracy**, **78.40% balanced accuracy**,
and **79.12% hate recall**, with **297 false blocks** and **124 missed hate posts**.

The lower accuracy did not mean that this second system was simply worse: it
caught more hate while blocking more non-hate. Policy owners must define which
trade-off is acceptable. The policy and cutoff both changed, so this contrast
must not be attributed to wording alone.

### F5. Jev still responds to policy authoring

In the original Jev study, HateXplain native-choice accuracy was **69.33%** with
the brief policy, **72.77%** with the detailed policy, and **75.16%** with four
training-selected examples added. The corresponding WildGuard figures were
**89.35%**, **90.05%**, and **90.17%**.

These are whole-policy comparisons. The detailed version added several kinds of
guidance together. They do not isolate one word, prove examples always help, or
explain Jev's internal mechanism. The threshold-tuned brief HateXplain control
already scored **79.47% ordinary accuracy**, so the full gain to **80.67%** cannot
be credited to better policy wording.

### F6. Validation requirements can fail on test

The false-block-limit profile selected configurations to maximize recall under
a 5% compliant-error limit on validation. None of its **17 eligible WildGuard
selections** met that limit on test; **16 of 18 HateXplain selections** did.
The separate 90%-recall profile met its test target for **0 of 18 WildGuard** and
**2 of 18 HateXplain** entries.

Among HateXplain entries meeting the 5% test limit, the highest observed recall
was **43.10%**. The two entries meeting the 90% catch target falsely blocked
approximately **42–43%** of non-hate posts.

These are results of separate validation-based selection procedures. They do
not imply that no other configuration could meet a target. Do not substitute a
better-looking test threshold after seeing these failures.

### F7. A native decision interface helps measurement, not proof of correctness

The Jev run returned **22,261 typed benchmark classifications** without failed
classifications. This gives us usable decision scores without a text parser.
It does not mean the decisions were all correct, the scores were calibrated on
every slice, or the architecture caused Jev's competitive performance.

Model size, training data, internal architecture, and development budgets differ
or are unknown. An architecture explanation remains a hypothesis.

## Essential context to carry with any table

1. The leaderboard covers **197 archived candidate records**, not 197 independent
   models or independent experiments. It reports **18 entries per benchmark**.
2. Common validation has **512 WildGuardTrain** and **1,920 HateXplain** examples.
   Tests have **1,699 WildGuardTest** and **1,924 HateXplain** examples. Selection
   used validation, not the maximum observed test score.
3. WildGuard measures prompt harmfulness only. HateXplain maps hate to BLOCK and
   offensive/normal to ALLOW. Neither benchmark establishes REVIEW quality,
   enterprise access control, multilingual deployment, or image moderation.
4. These public tests were already inspected in earlier studies. This is
   retrospective, exploratory evidence. Policy searches and prior training
   exposure were not matched across models.
5. WildGuardTrain has model-derived labels; the official test has human labels
   and a different mixture. WildGuard itself trained on WildGuardTrain. A
   validation-to-test gap cannot be assigned to one cause from these results.
6. Nine unresolved Safeguard test responses remain errors. Missing results and
   categorical models' unavailable score metrics remain visible. The four
   frontier API pilots are unranked because they lack full validation/test runs.
7. The leaderboard used saved predictions and **$0 new inference spend**.
   All **140** calibrator/combiner replays matched archived predictions. The
   original Jev extension cost **$0.424208**, including its connectivity check.
   Those bills are not a matched cost-per-correct-decision comparison.

## How to use this in each document

For the research paper, add the retrospective selection protocol, balanced and
operating-target results, paired uncertainty, and the Jev extension. Preserve the
distinction between policy changes, threshold changes, and fitted combinations.
Keep frontier API pilots in the appendix, as previously requested.

For the magazine article, use F4 as a worked example: the team changed the goal,
and a different policy/cutoff combination became preferable. Explain what a false
block means to a user and what a missed violation means to a moderator. Then use
F5 and F6 to show why policy authors and engineers need a shared testing process.

For the media article and learning skill, lead with the changing responsibility:
natural-language policy is an operational artifact that requires versioning,
tests, and accountable decisions about mistakes. Use a small number of supporting
figures with their task and metric; link to the detailed archive for the rest.
Do not describe untested local decision models as validated replacements.
