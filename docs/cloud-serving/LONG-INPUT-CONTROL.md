# Does a short-prompt serving choice carry to long inputs?

This exploratory control was specified after observing the primary length
curves. It is not another primary selection or an untouched test-set comparison.
Both engines selected a 2,048-token chunk using the original short fitting
prompts. Keep those selections and their complete curves unchanged.

Measure the other predeclared candidate, 8,192 tokens, on the same 64 synthetic
4,096-content-token inputs, at concurrency 1 and 8, with two repeats. Use the
same request order seeds, policy, input IDs, generation contract, BF16 weights,
cache settings and L4. Run engines serially after the primary and specialist
canary work. Keep the same two-hour provider limit and $1.22 study ceiling.

Report both primary and control results, including failures, without replacing
the original choice with whichever is faster. This asks whether one tuning
workload represents another; it does not demonstrate optimal settings for long
documents. It uses no benchmark labels and makes no new accuracy claim.
