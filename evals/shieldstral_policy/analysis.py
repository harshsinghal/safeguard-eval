"""Offline test-blind cutoff selection and paired benchmark reporting."""
import argparse
from collections import defaultdict
import math
from pathlib import Path
from statistics import mean

from evals.enterprise_benchmark.scoring import track_metrics
from evals.liquid_router.common import read, rows, write
from .runtime import SEED

LABELS = ("ALLOW", "BLOCK")
GRID = tuple(i / 20 for i in range(1, 20))


def prediction(row, cutoff):
    if row["score"] is None:
        return "ERROR"
    return "BLOCK" if row["score"] >= cutoff else "ALLOW"


def split_tracks(records):
    tracks = defaultdict(list)
    for row in records:
        tracks[row["track"]].append(row)
    return tracks


def metrics(records, cutoff):
    by_id = {r["id"]: {"prediction": prediction(r, cutoff)} for r in records}
    output = {}
    for track, members in split_tracks(records).items():
        labels = tuple(label for label in LABELS if any(r["expected"] == label for r in members))
        output[track] = track_metrics(members, by_id, labels)
    return output


def macro(tasks, key):
    values = [t[key] for t in tasks.values() if t[key] is not None]
    return mean(values) if values else None


def operating(tasks):
    block_recalls = [t["per_class"]["BLOCK"]["recall"] for t in tasks.values() if "BLOCK" in t["per_class"]]
    return macro(tasks, "false_block_rate"), mean(block_recalls)


def select(records):
    options = {cutoff: metrics(records, cutoff) for cutoff in GRID}
    tie = lambda c: (-abs(c - 0.5), -c)
    optimum = max(GRID, key=lambda c: (macro(options[c], "balanced_accuracy"), *tie(c)))
    rates = {c: operating(m) for c, m in options.items()}
    feasible = [c for c, (fp, _) in rates.items() if fp <= 0.10]
    control = max(feasible, key=lambda c: (rates[c][1], *tie(c))) if feasible else None
    return {
        "balanced": optimum, "validation_balanced_accuracy": macro(options[optimum], "balanced_accuracy"),
        "low_false_block": control, "validation_low_false_block_operating_point": rates.get(control),
    }


def same_cases(left, right):
    keys = ("id", "track", "audit_group", "expected", "input_sha256", "policy_sha256", "tokens")
    signature = lambda rs: {r["id"]: tuple(r[k] for k in keys) for r in rs}
    if len(left) != len(signature(left)) or len(right) != len(signature(right)) or signature(left) != signature(right):
        raise ValueError("Comparison cohorts differ")


def group_bootstrap(base, other, base_cut, other_cut, primary):
    import numpy as np

    keyed = {r["id"]: r for r in other}
    cells = [(task, label) for task in sorted(primary) for label in LABELS]
    group_stats = defaultdict(lambda: np.zeros((2, len(cells)), dtype=np.int32))
    for row in base:
        if row["track"] not in primary:
            continue
        cell = cells.index((row["track"], row["expected"]))
        group = group_stats[row["audit_group"]]
        group[0, cell] += 1
        group[1, cell] += (int(prediction(keyed[row["id"]], other_cut) == row["expected"])
                          - int(prediction(row, base_cut) == row["expected"]))
    array = np.stack(list(group_stats.values()))
    rng = np.random.default_rng(SEED)
    results = []
    for _ in range(4000):
        sampled = array[rng.integers(len(array), size=len(array))].sum(axis=0)
        if sampled[0].min() > 0:
            results.append((sampled[1] / sampled[0]).mean())
    if len(results) < 3900:
        raise ValueError("Too few valid bootstrap replicates")
    return {"interval": np.quantile(results, [0.025, 0.975]).tolist(),
            "resamples": len(results), "groups": len(group_stats)}


def matched_roc(records, target):
    # Sweep complete tie blocks. Macro weighting equals weighting each
    # labeled example by the inverse number of its task's reference class.
    size = {(t, l): sum(r["expected"] == l for r in rr)
            for t, rr in split_tracks(records).items() for l in LABELS}
    tasks = {l: sum(1 for (t, label), n in size.items() if label == l and n) for l in LABELS}
    changes = defaultdict(lambda: {"ALLOW": 0.0, "BLOCK": 0.0})
    for row in records:
        if row["score"] is not None:
            label = row["expected"]
            changes[row["score"]][label] += 1 / (size[row["track"], label] * tasks[label])
    fp = tp = 0.0
    for score in sorted(changes, reverse=True):
        change = changes[score]
        if fp + change["ALLOW"] > target + 1e-12:
            break
        fp += change["ALLOW"]
        tp += change["BLOCK"]
    return {"false_block_rate_at_or_below_target": fp, "block_recall": tp}


def summarize(state):
    frozen = read(state / "freeze.json")
    all_results = {s: rows(state / "evaluation" / f"{s}.jsonl") for s in frozen["cutoffs"]}
    base = all_results["base"]
    for rr in all_results.values():
        same_cases(base, rr)
    suite = {s: [r for r in rr if r["track"] != "policy_contrast"] for s, rr in all_results.items()}
    cutoffs = {s: c["balanced"] for s, c in frozen["cutoffs"].items()}
    base_metrics = metrics(suite["base"], cutoffs["base"])
    target_fp = macro(base_metrics, "false_block_rate")
    primary = {t for t, m in base_metrics.items() if m["balanced_accuracy"] is not None}
    result = {"primary_tasks": sorted(primary), "benchmark_cases": len(suite["base"]), "systems": {}}
    for system, records in suite.items():
        cutoff = cutoffs[system]
        calibrated = metrics(records, cutoff)
        lower = frozen["cutoffs"][system]["low_false_block"]
        fresh = [r for r in all_results[system] if r["track"] == "policy_contrast"]
        pair_accuracy = lambda c: sum(all(prediction(r, c) == r["expected"] for r in rr)
                                      for rr in split_pairs(fresh).values())
        stats = {
            "cutoff": cutoff,
            "equal_task_balanced_accuracy": macro(calibrated, "balanced_accuracy"),
            "macro_false_block_rate": macro(calibrated, "false_block_rate"),
            "macro_block_recall": operating(calibrated)[1],
            "tasks": calibrated,
            "fixed_half_tasks": metrics(records, 0.5),
            "low_false_block_cutoff": lower,
            "low_false_block_test_operating_point": operating(metrics(records, lower)) if lower is not None else None,
            "matched_roc_at_base_test_false_block_rate": matched_roc(records, target_fp),
            "fresh_pairs": len(split_pairs(fresh)), "fresh_pairs_correct": pair_accuracy(cutoff),
            "fresh_pairs_correct_fixed_half": pair_accuracy(0.5),
        }
        if system != "base":
            changes = {t: calibrated[t]["balanced_accuracy"] - base_metrics[t]["balanced_accuracy"] for t in sorted(primary)}
            recall_changes = {t: calibrated[t]["per_class"]["BLOCK"]["recall"] - base_metrics[t]["per_class"]["BLOCK"]["recall"]
                              for t in sorted(primary)}
            paired = group_bootstrap(suite["base"], records, cutoffs["base"], cutoff, primary)
            stats["paired_vs_base"] = {
                **paired, "delta": mean(changes.values()), "task_deltas": changes, "block_recall_deltas": recall_changes,
                "criterion_met": paired["interval"][0] > 0 and sum(v > 0 for v in changes.values()) >= 3
                and min(changes.values()) >= -0.05 and min(recall_changes.values()) >= -0.10,
            }
        result["systems"][system] = stats
    return result


def split_pairs(records):
    pairs = defaultdict(list)
    for row in records:
        pairs[row["audit_group"]].append(row)
    if any(len(rr) != 2 or {r["expected"] for r in rr} != set(LABELS) for rr in pairs.values()):
        raise ValueError("Fixture pair lost its counterfactual")
    return pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    write(args.output, summarize(args.state))
