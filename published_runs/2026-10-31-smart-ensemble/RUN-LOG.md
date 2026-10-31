# Smart ensemble run log

## Before fitting

- Registered the fixed candidate pool, group-disjoint fitting/validation populations,
  five-fold selection, four-component limit, controls, thresholds and budget in
  commit `f354168`. Both official public tests were explicitly designated reused.
- Verified native cached-score identities and policy hashes against frozen evidence.
  Seven candidate configurations are eligible for WildGuard; six for HateXplain.
  Original decision-policy development groups do not overlap the new fitting or
  validation populations. No test outcome was used to choose the new system.
- Reserved at most $1 in API costs and $2.40 for a three-hour GPU run. Prior
  cumulative spending was $15.26540555656 against the authorized $20 cap.
- Started one GPU.ai L40S at $0.80/hour with a three-hour automatic termination
  limit. RunPod capacity was not needed. Separate pinned environments preserve
  the existing Kev and Clef adapters. The Kev environment needed the original
  Pydantic dependency restored before inference.
- The first Jev canary used an exported policy pack with redacted examples.
  Restored and hash-verified the exact private payloads before bulk inference.
  The corrected 16 WildGuard requests reproduced all historical request hashes,
  but scores still varied by up to .05; HateXplain canaries varied by up to .06.
  Neither canary changed a native decision. This led to a pre-fit amendment to
  recollect Jev test outputs only after freezing, using the same policy packs.
- One empty WildGuard fitting prompt is retained as an unresolved input for the
  three decision models. No substitute content or label was invented. Other
  component scores remain usable for methods that do not require the missing ones.
- Four Jev HateXplain validation calls failed with `URLError`. No response or score
  was available. Their maximum reserved costs are retained as upper bounds; each
  retry has a separate ledger entry. Successful responses are reused, never
  resampled to obtain a preferred score. Three total attempts per request is the
  frozen limit. See AMENDMENTS.md and transport-reconciliation.json.
- Implemented fitting, validation selection, freeze checks, paired evaluation and
  CPU reproduction. Synthetic checks cover identity alignment, duplicate groups,
  subset-specific unresolved inputs, coefficient reconstruction, freeze tampering
  and separate retry charges. They use no benchmark test outcomes.

Final fitting, freeze, test, billing and reproduction events are recorded below
when they occur. Provider response bodies and source content remain private.

## Native scoring and resource shutdown

- All Kev/Clef fitting, validation and canary scores were collected and aligned. Native canary maximum score differences were .01177/.01058 for Kev and .01018/.00363 for Clef (WildGuard/HateXplain), below the fixed .02 tolerance; no native decisions changed.
- Runtime environments, logs, manifests and the exact native inference source were preserved and scanned for credentials.
- GPU.ai instance was confirmed terminated; billed GPU time was 2,447 seconds and cost $0.54. Temporary provider/local SSH keys were removed. A collection-command correction used uv to export package versions; inference was already complete.
- Strict development alignment verified all seven WildGuard and six HateXplain configurations. Only the single empty WildGuard fitting prompt is unresolved, for the three decision models.

## Fitting and freeze

- Fitting completed locally with one numerical thread. WildGuard retained Shieldstral alone; its best attempted addition did not improve OOF balanced accuracy. HateXplain retained Jev, Shieldstral and Kev; adding Clef did not reach the required 0.2-point gain.
- Full component paths, rejected additions, coefficients, validation choices and artifacts were frozen before test scoring. Public freeze commit: `a2ef18e`. No test-score files existed at that boundary.
- Fresh Jev test inference started only after the freeze commit was pushed. Other components will use their registered archived test outputs, verified by hashes. No configuration will be changed from test feedback.

## Final evaluation and reproduction

- All 3,623 fresh Jev test requests completed after the freeze; no test transport retries were needed. Registered archived test sources passed their hashes and all configured test populations aligned.
- Primary results: WildGuard retained Shieldstral, 90.53% balanced accuracy, 60 false blocks and 95 misses. HateXplain retained Jev/Kev/Shieldstral, 79.97%, 282 false blocks and 112 misses. No post-test retuning or primary replacement occurred.
- HateXplain primary versus its selected Jev individual: +1.55 points (paired interval -0.04 to +3.14); 86 fewer false blocks and 20 more misses. Versus all-model equal log-odds averaging: +2.14 points (1.00 to 3.29), 48 fewer false blocks and four fewer misses.
- All-model learned controls and all negative results remain in the tables. The WildGuard equal-average improvement remained uncertain. Operational-target profiles failed on WildGuard and required large tradeoffs on HateXplain.
- Local CPU reproduction matched every selection, coefficient, score, metric and paired interval; maximum score difference was zero on both datasets.
- Final accounted cost: $1.424612316, including $0.54 GPU, $0.873602268 reported API charges and $0.011010048 for four unknown-cost transport attempts at their reserved maximum. Cumulative accounted spending: $16.69001787256, leaving $3.30998212744. No GPU remains for this study.
- A second CPU reproduction using only the exported source and public score files also passed with zero score difference. No provider calls were made.
