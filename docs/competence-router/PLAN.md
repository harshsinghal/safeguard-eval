# Learning which guard is likely to succeed

Status: registered local experiment; no publication or Git push authorized.

Use the pinned pretrained Liquid LFM2.5 encoder, frozen on CPU, and four independent
L2 logistic heads to predict guard correctness under the caller's trusted policy.
Targets are four simultaneous binary outcomes, not an arbitrary single winner.
Technical errors are masked during semantic competence fitting and counted wrong
in system evaluation. The existing category classifier remains a comparison arm.

Before fresh predictions, select 64 records per family from the archived Liquid
fitting pool (448); add the original 192 calibration records as development data.
Reuse those 192 paired guard outputs only after checking input, policy, model and
adapter identities. Select two disjoint 16-per-family panels from the archived
Liquid validation pool (112 validation, 112 test), assigning whole audited groups
by stable hash before stratified sampling. These records were seen in earlier
category-classifier validation, so this is a new competence-routing holdout, not
a completely fresh benchmark. Original fixed evaluation/pilot remain immutable.
Protect all frozen benchmark calibration/test groups and exact/near duplicates
using the existing source audit. Reaudit development boundaries jointly and
exclude lower-priority records. Preserve exclusions and source/data/code hashes.

Encoder view: separate bounded prompt (256 tokens) and policy (192 tokens) views,
joined with separator tokens, with masked mean pooling. Semantic policy fields
only (purpose, precedence, allow, block, review), plus the decision label contract;
no benchmark name, ID, source ID, gold label, or guard output enters features.
Retain ten simple input structure/length features. Guards receive full input.
Policy truncation is explicit; long-context loss remains a limitation.

Fit StandardScaler and four logistic heads on development only. Select C from
[0.01, 0.1, 1.0] by validation mean binary log loss. For deterministic constant
heads use a Laplace-smoothed development success rate. No encoder fine-tuning,
INT8 sweep, guard policy/threshold changes or model downloads are part of this run.
Use Clef as the fixed default. Supported policies require >=16 fitting and >=8
validation examples; unseen/changed policies and unsupported ternary policies
fall back to Clef. Choose switching margin from [0, .05, .10, .20, 1.01] on
validation raw system accuracy, preferring fewer switches then larger margin on
ties. Nondefault guards must have >=8 validation switches and a positive 90%
group-bootstrap lower confidence bound of paired accuracy improvement on their
switched cases (1000 resamples, fixed seed). The combined selected route must
also have a positive lower bound vs Clef, otherwise freeze default-only. This is
a conservative selection heuristic, not a generalization guarantee. Report all
validation candidates, calibration error/Brier/log loss, not just the winner.

Compare on the reserved test: Clef, the frozen original category router, a
conservative policy-category control selected by the same paired validation
criterion, and learned competence routing. Report raw accuracy, available-task
balanced recall, per-task/class errors, coverage, paired group bootstrap intervals,
and official enterprise profiles only when every reference task/class is present.
Do not renormalize missing official profiles. Also evaluate the exposed 112-case
pilot separately as a diagnostic, never a confirmatory improvement claim.
Freeze selection and checkpoint hashes before opening test guard outcomes.
Run actual /moderate requests for the reserved test, checking counterfactual
control agreement. Group scheduling amortizes cold loads and is not natural
traffic latency. Every input reaches a guard, including router errors/uncertainty;
backend failure tries the default and unresolved errors remain failed REVIEW.

Use cached models and existing native workers, four CPU threads, one GPU guard at
a time, BF16, microbatch one and software 20% operation duty. No clock/power limit
changes or paid compute. Durable external 0.5s device sampling supplements worker
thermal/power checks (cooldown >60C or >180W; stop >=70C or three >250W samples).
Limit fresh guard collection to 90 minutes, CPU fitting to 15 minutes, actual
routed evaluation to 20 minutes. Unload all study GPU workers and retain receipts.
Record negative results rather than claiming the implementation guarantees a win.
