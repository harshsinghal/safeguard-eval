# Maintaining the living research notebook

The [main README](../README.md) is the chronological entry point to the research.
It should explain what question each experiment addressed, what changed, what
happened, and what a practitioner can learn. Detailed methods and evidence live
in linked study folders; the original application lives in [DEMO.md](../DEMO.md).

## Adding a completed experiment

1. Publish a dated evidence bundle under `published_runs/`. Include the exact
   policies, model revisions, native adapters, data splits, selection objective,
   saved predictions, analysis, and material failures. Check publication rights
   and keep credentials and private user conversations out of the archive.
2. Write a readable study summary under `docs/`, including policy edits, error
   trade-offs, limitations, compute use, and reproduction instructions.
3. Add an experiment-named entry to the README log. Use the research question or
   method as its heading, without a date. Keep entries in experiment order.
   Distinguish ordinary accuracy,
   balanced accuracy, and macro-F1; identify which settings were held fixed.
   Label pilots, proposals, synthetic demonstrations, and reused-test analyses.
4. Link the summary and frozen evidence from that entry. Preserve the historical
   result even if a later selection objective produces a different score.

Do not rewrite frozen results. Publish corrections or extensions separately,
explain the difference, and link both versions. Dates belong in provenance and
immutable archive names; they need not lead the README headings. A new study
does not automatically update the downloadable skill, paper, or other articles.

## Updating the leaderboard

The README tables are generated from a single frozen `results.json`, currently
the integration of the decision-model ensembles with the earlier studies. Do not type new scores into the
README or choose each model's largest observed test score.

After reviewing and publishing a new leaderboard archive, update `SOURCE` in
[`tools/update_readme_leaderboard.py`](../tools/update_readme_leaderboard.py),
then run:

```bash
python3 tools/update_readme_leaderboard.py
python3 tools/update_readme_leaderboard.py --check
git diff --check
```

The script only formats saved results; it makes no inference calls and changes
no selection or threshold. Review the surrounding prose separately: study scope,
candidate counts, denominators, ensemble membership, uncertainty, and links may
also need to change. The [metric guide](leaderboard/METRICS.md) must match the
scoring implementation. GitHub CI checks that the generated tables are current.

## Keeping the skill reproducible

A released skill is a dated, pinned evidence snapshot. Current research may move
ahead while that release remains intact. The README must disclose its evidence coverage
and route readers to newer studies directly. Package checks validate the
skill against its pinned Git revision; preparing a new evidence snapshot requires
a separate review and refresh. Follow the [skill maintenance guide](skill/MAINTAINING.md)
when making a new release. Do not move existing tags or silently replace a release.
