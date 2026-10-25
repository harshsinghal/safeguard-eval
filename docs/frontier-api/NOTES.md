# Frontier API lab notebook

## 2026-10-25 — setup, no inference results

User requested frontier OpenAI, Anthropic, and open-weight API comparisons through OpenRouter, with reasoning controls and the established policy-tuning process. Checked official OpenAI/Anthropic guidance and OpenRouter's live model and endpoint catalogs. Preserved the four-model snapshot. Both chosen closed-model flagships require reasoning, so their lower condition is **low**, not off. DeepSeek and Kimi advertise **none** support. All capability claims still need an inference pilot.

Found the locally supplied OpenRouter credential and authenticated only through `GET /api/v1/key`. Account details stay in ignored local work files. Key availability and account credit do not change the approved project budget.

Reused historical dataset hashes and request formatting. Registered three inherited prompts per condition; the two new candidates per condition remain unwritten until new fitting errors are available. Existing studies and their frozen evidence were not modified. Prepared free local cost estimation, a strict-output API runner, durable billing reservations, phase approval checks, and selection/freeze/analysis tools. Added tests covering malformed outputs, reasoning controls, budget persistence, unknown billing, changed data/source/policies, and selection reproducibility.

The full same-sized process is expensive at frontier API rates: at most 116,808 requests including controls and repeats. Estimated short/moderate reasoning totals are about $1,144/$3,344 before discounts. A proposed 256-request pilot is about $2.40/$7.22 under those assumptions; long reasoning could exceed a $10 pilot limit. These are estimates from request lengths and catalog prices, **not measured costs**. Current setup incurred **$0 new inference cost** and produced **no accuracy/F1 results**. Cumulative recorded experimental spend remains $7.91.

Local verification: all 35 repository tests pass, including nine frontier-study tests. Documentation links and whitespace checks pass. Simulated API responses test successful billing and unresolved-cost stops; they are test fixtures, not real model results.

Next: obtain explicit authorization for the proposed $10 pilot phase, interleave conditions, record actual behavior/cost, and then finalize the full-study budget. Do not start the full search merely because a pilot budget was approved.

## Evidence to retain for articles and research

Keep a dated entry for every policy hypothesis, fitting error pattern, exact before/after text, candidate hash, validation result, rejection, protocol amendment, and infrastructure failure. Publish both improvements and regressions. Preserve provider identity and billing metadata so future writing can distinguish policy effects, reasoning effects, and deployment changes. Raw gated dataset text and model traces stay private; publish prompt-free predictions and reproducible metrics. Treat all comparisons as exploratory because the earlier official-test results are already known.

## 2026-10-25 — pilot authorized

User authorized a $20 spending limit. Interpret this as the cumulative project limit, including the $7.91 already spent. Retain the proposed $10 cap for this pilot phase, leaving $2.09 of additional project headroom even if the entire pilot allowance is used. Full search remains a separate, unstarted phase. Record source/catalog checks and account usage before the first paid request.
