# Qwen comparison lab notebook

## 2026-10-25 UTC — protocol and model selection

The user requested nearby-size general-purpose Qwen instruction models as a comparison with the five policy/WildGuard deployments. Qwen3.5 has 2B, 4B, 9B and 27B dense language models and a 35B-total/3B-active mixture-of-experts model. CoPE is 25.2B total / 3.8B active, so treating it as an ordinary 4B model would be misleading. Safeguard is also a mixture-of-experts model. Both receive separate total-size and active-size comparisons.

The policy document is itself an instruction. We preserve its substantive text and render it in a general-purpose model's system message; model specialization and deployment differ. The original policy files, predictions and study remain immutable. Prior test results are already known to the experimenter, so all new conclusions are exploratory. Reusing the same test enables paired comparisons but does not restore an unseen holdout.

No new paid resources are active at protocol drafting. Existing spend is $5.87, leaving at most $4.12 under the original cap. The planned main deployment disables Qwen thinking explicitly, uses free-generated binary letters, and counts refusals/truncations/invalid output as errors. Its output format and runtime differ from native policy classifiers; these are system comparisons.

## Pre-inference implementation checks

Pinned all five Qwen checkpoint revisions and their full checkpoint parameter counts (2.274B, 4.660B, 9.653B, 27.781B, 35.952B). The advertised language-model sizes exclude some vision-related weights. All 26 local tests pass, including strict classification parsing, rejecting refusals and truncations, separation of policy and submitted text, and rejecting changed frozen sources, policies or populations. Historical WildGuard code and artifacts are unchanged. GPU.ai reports $19.50 credit, no active instances, and an available secure 96 GB RTX PRO 6000 VM at $1.99/hour including disk. Credit availability does not increase the user cap.
