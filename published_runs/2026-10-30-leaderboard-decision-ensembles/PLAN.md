# Integration procedure: decision-model combinations in the common leaderboard

This procedure documents a publication step after both source studies were
complete. It is not a preregistration or a new held-out experiment.

1. Verify the checksums of the previous 20-entry leaderboard and decision-score
   ensemble study. Read their saved outputs; make no inference calls or fits.
2. Preserve all earlier entries and their validation choices. Recompute the
   original validation grids to verify those choices without changing them.
3. Require identical WildGuard example order, IDs, labels, text hashes, groups,
   subcategories, and adversarial status before combining positional outputs.
4. Add nine method families for each decision-model cohort: seven score methods
   and two decision-only controls. Keep all fitted hyperparameter candidates
   within each family. Copy the frozen validation selections and verify them by
   recalculating selection on the common 512-example validation population.
5. Exclude “best method” aliases and the source experiment's individual
   calibration controls from added leaderboard rows. Do not revise earlier
   individual-model pools after observing their test results. Explain the
   difference between the earlier three-policy pools and new two-policy pool.
6. Score the copied operating points on the same 1,699 WildGuardTest prompts and
   preserve all 1,924 HateXplain cases. Keep unresolved responses in denominators.
7. Verify every previous result except its displayed rank and every added
   classification result against its source. Calibration losses remain in the
   source study; the common report retains classification and ranking metrics.
8. Recompute shared paired bootstrap intervals and all cross-study comparisons.
   Render tables, CSV, and offline HTML. Publish as a new immutable archive;
   leave both input archives unchanged. Report the primary method separately
   from secondary methods, including any with higher observed test scores.

Selection still uses the same three validation objectives: balanced accuracy,
a 5% compliant-error limit, and a 90% violation-catch target. An infeasible
categorical control remains a gap. No test outcome selects a new method,
policy, threshold, or fitting parameter.

Candidate accounting: 209 previous records plus 52 decision-combination records
equals 261. Entry accounting: 20 previous WildGuard entries plus 18 new entries
equals 38; HateXplain stays at 20. These counts are not unique-model counts.
