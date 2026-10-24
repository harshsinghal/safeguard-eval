# WildGuard lab notebook

Append dated entries; retain failed attempts and protocol deviations. Do not include credentials or gated prompt text.

## 2026-10-24 — protocol and access

The user authorized implementation, supplied Hugging Face and Runpod credentials in the local KEYS directory, and requested durable research notes. The earlier total spending cap remains $10; prior billed compute is $1.57. Existing arena results are exploratory and do not answer the WildGuard policy-tuning question.

Protocol saved before new inference. Hugging Face model config access succeeds. Dataset repository metadata is accessible; file access and pinned download are next. No paid resources have been created for this study. Existing GPU.ai instance list is empty.

## 2026-10-24 — dataset preparation and adapter decisions

Pinned dataset revision d29c47f41c8b51348b5c8e8c81c039b3132b66d1; training parquet SHA256 02ecea8a724a9146a1e473a95a7cdf262adfe9c7d5408953ca86d2fcfbdc8953. All 86,759 training rows have binary prompt labels. Fourteen prompts are empty strings (13 unharmful, one harmful); retained as valid source rows and grouped together, rather than silently removed. An initial strict nonempty check caught these before inference and was corrected to preserve population.

Training partitions: 69,366 fit, 8,700 validation, 8,693 audit. Exact and approximate near-duplicate grouping details and strata are in data-manifest.json. Approximate retrieval does not guarantee all semantic duplicates were found. The official test has not been fetched.

Initial policy p0 covers the original taxonomy and benign exceptions. WildGuard uses official completion format and one tokenizer-added BOS. All policy models use binary ALLOW/BLOCK; native score thresholds are 0.5. PolicyLM retains upstream cleaner/windowing, fixes max_batch_rows=1 for reproducibility, and disables the character cap to avoid silently truncating long prompts. This adapter choice is fixed before observing pilot results. Safeguard uses medium reasoning with a 4,096-token cap and a short JSON reason; cap exhaustion counts as ERROR. HTTP concurrency is 32.

GPU.ai credit balance was $23.80, but the study still respects the earlier total spending cap. RTX PRO 6000 96GB offer 27740f2244eb is $1.99/hour and was reliable in the earlier run; a four-hour provider termination limit bounds new instance compute to $7.96. No Runpod spend is needed while GPU.ai credit suffices.
