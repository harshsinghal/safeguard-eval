# Expanded balanced leaderboard: Kev and Clef added

Open [the interactive comparison](index.html), [all tables](RESULTS.md), or [the CSV](leaderboard.csv). Read the [new experiment's findings](../../docs/decision-models/README.md).

This extension has **20 entries per benchmark**, drawn from **209 eligible candidate records**. It adds Kev 4B and Clef-Flash 9B on the same 1,699 WildGuardTest prompts and 1,924 HateXplain posts. The previous 18 entries, validation selections, metrics, and confidence intervals are unchanged; their displayed ranks can move.

| Model | WildGuard balanced accuracy | HateXplain balanced accuracy |
|---|---:|---:|
| Jev 1.14 | 88.69% | 78.40% |
| Clef-Flash 9B | 87.62% | 74.94% |
| Kev 4B | 86.93% | 75.17% |

The earlier ensembles still have the highest observed balanced scores: 91.08% on WildGuard and 79.35% on HateXplain. The interactive comparison supplies paired uncertainty, not just rank order. Jev's WildGuard difference from Clef is not clearly resolved by these data.

The new models used three policy candidates each. Policy and cutoff selection used only validation, with a frozen record before new test inference. Old selections are copied from the [original leaderboard](../2026-10-29-leaderboard/README.md). Public tests had already been used in prior studies; this is exploratory evidence with unequal historical search budgets. No model weights or ensemble parameters were trained for this extension.

## Reproduce without inference

Install `requirements.txt` in a Python environment. From this folder:

```sh
PYTHONPATH=source python -m evals.leaderboard.build reproduce --bundle .
```

The command recomputes validation choices, test metrics, category slices, bootstrap intervals, and all paired comparisons from the included normalized outputs, then requires exact equality with `results.json`. No API keys, model weights, GPUs, or benchmark text downloads are needed.

[selection.json](selection.json) identifies each operating point. [registry.json](registry.json) identifies candidate systems. [freeze.json](freeze.json) connects this extension to the pre-test decision-model freeze and the immutable prior archive. [extension-provenance.json](extension-provenance.json) records that previous entries are unchanged. [coverage.json](coverage.json) keeps fitting-only frontier API pilots unranked and displays missing evaluations.

The accompanying [experiment archive](../2026-10-29-decision-models/README.md) contains the policies, training-example provenance, native probabilities/logits, runtime manifests, and the $0.87 billing and verified shutdown records.
