"""Build/reproduce the balanced leaderboard from saved outputs; no inference.

The prepare command freezes validation-only choices. Evaluate refuses changed
inputs and uses those choices unchanged. Reproduce uses normalized public data.
"""
import argparse
import csv
import datetime
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from evals.leaderboard.archive import Archive, ARCHIVES, MODELS, digest, read, write
from evals.leaderboard.metrics import PROFILES, bootstrap, decisions, eligible, interval, metrics, select

DATASETS = ("wildguard", "hatexplain")
PROFILE_NAMES = {"balanced": "Balance both classes", "false_block_limit": "False-block limit: 5%",
                 "catch_target": "Violation-catch target: 90%"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def prepare(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if (destination / "freeze.json").exists():
        raise ValueError("Selection is already frozen; use a new destination")
    destination.mkdir(parents=True, exist_ok=True)
    archive = Archive(root)
    archive.discover_raw()
    archive.discover_fitted()
    selections, grids = {}, {}
    for dataset in DATASETS:
        meta = archive.metadata[dataset]["validation"]
        specs = {cid: s for cid, s in archive.specs.items() if s["dataset"] == dataset}
        values = {cid: archive.values(s, "validation") for cid, s in specs.items()}
        write(destination / "validation" / f"{dataset}.json.gz", dict(metadata=meta, candidates=values))
        y = [int(r["expected"] == "BLOCK") for r in meta]
        groups = defaultdict(dict)
        for cid, v in values.items():
            groups[specs[cid]["group"]][cid] = v
        selections[dataset], grids[dataset] = {}, {}
        for group, candidates in sorted(groups.items()):
            best, grid = select(y, candidates)
            selections[dataset][group] = dict(choices=best, candidates=len(candidates))
            grids[dataset][group] = grid
        print(f"Selected {dataset}: {len(specs)} archived candidates; {len(groups)} leaderboard entries", flush=True)
    coverage = archive.coverage()
    write(destination / "registry.json", archive.specs)
    write(destination / "coverage.json", dict(models=coverage, exclusions=archive.excluded,
          candidate_counts=dict(Counter(s["dataset"] for s in archive.specs.values())),
          historical_results={k: f"published_runs/{v}/README.md" for k, v in ARCHIVES.items()},
          grouping_note="Jev HateXplain exports omit group IDs; exact-matched original dataset groups govern bootstrap resampling."))
    write(destination / "validation-grid.json.gz", grids)
    write(destination / "selection.json", selections)
    code_files = list((root / "evals/leaderboard").glob("*.py")) + [root / p for p in (
        "evals/ensemble/common.py", "evals/ensemble/learn.py", "evals/ensemble_logits/learn.py")]
    for path in code_files:
        archive.track(path)
    protocol = root / "docs/leaderboard/PLAN.md"
    archive.track(protocol)
    artifacts = ["registry.json", "coverage.json", "validation-grid.json.gz", "selection.json"] + [f"validation/{d}.json.gz" for d in DATASETS]
    freeze = dict(created_utc=now(), status="frozen before new test scoring", analysis_role="retrospective exploratory reanalysis",
                  primary="balanced_accuracy", profiles=PROFILE_NAMES, input_hashes=archive.inputs,
                  artifact_hashes={p: digest(destination / p) for p in artifacts},
                  validation_n={d: len(archive.metadata[d]["validation"]) for d in DATASETS},
                  expected_test_n={d: len(archive.metadata[d]["test"]) for d in DATASETS},
                  no_new_inference=True, no_new_fitting=True,
                  note="Earlier test results were already known. Candidate availability and prior training/search budgets differ.")
    write(destination / "freeze.json", freeze)
    shutil.copy2(protocol, destination / "PLAN.md")
    print(f"Frozen selections: {destination / 'freeze.json'}", flush=True)


def check_freeze(bundle, root=None):
    freeze = read(bundle / "freeze.json")
    for p, sha in freeze["artifact_hashes"].items():
        if digest(bundle / p) != sha:
            raise ValueError("Changed selection/development artifact: " + p)
    if root is not None:
        for p, sha in freeze["input_hashes"].items():
            if digest(Path(root) / p) != sha:
                raise ValueError("Changed original input: " + p)
    return freeze


def score_bundle(bundle):
    """Score frozen choices. This function never selects or changes a cutoff."""
    freeze = check_freeze(bundle)
    specs, selection = read(bundle / "registry.json"), read(bundle / "selection.json")
    result = dict(analysis_role=freeze["analysis_role"], primary_metric="balanced_accuracy", datasets={})
    for dataset in DATASETS:
        test = read(bundle / "test" / f"{dataset}.json.gz")
        meta, candidates = test["metadata"], test["candidates"]
        if len(meta) != freeze["expected_test_n"][dataset]:
            raise ValueError("Changed official test population")
        y = [int(r["expected"] == "BLOCK") for r in meta]
        profiles, all_predictions = {}, {}
        for profile in PROFILES:
            rows, gaps = [], []
            for group, selections in selection[dataset].items():
                chosen = selections["choices"][profile]
                if chosen is None:
                    gaps.append(dict(group=group, reason="No archived candidate meets this requirement on validation"))
                    continue
                cid, t = chosen["candidate"], chosen["threshold"]
                spec, values = specs[cid], candidates[cid]
                p = decisions(values, t)
                key = profile + "/" + group
                all_predictions[key] = p
                m = metrics(y, p, values.get("score"))
                native = metrics(y, values["prediction"])
                row = dict(key=key, group=group, candidate=cid, label=spec["label"], category=spec["category"],
                           model_id=spec["model_id"], policy=spec["policy"], adapter=spec.get("adapter", "frozen fitted score combiner"),
                           source_archive=spec["source_archive"], candidate_count=selections["candidates"],
                           threshold=t, validation=chosen["metrics"], metrics=m, native_reference=native,
                           test_requirement_met=eligible(m, profile), fitting_rows=spec.get("fitting_rows"),
                           validation_rows=spec["validation_rows"], slice_metrics={})
                for field in ("subcategory", "adversarial", "source_label", "platform", "agreement"):
                    if any(field in r for r in meta):
                        row["slice_metrics"][field] = {}
                        for value in sorted({str(r.get(field)) for r in meta}):
                            ix = [i for i, r in enumerate(meta) if str(r.get(field)) == value]
                            row["slice_metrics"][field][value] = metrics(np.array(y)[ix], p[ix])
                rows.append(row)
            # Ordering is descriptive presentation, never a configuration choice.
            if profile == "false_block_limit":
                rows.sort(key=lambda r: (not r["test_requirement_met"], -r["metrics"]["recall"], r["metrics"]["compliant_error_rate"], r["group"]))
            elif profile == "catch_target":
                rows.sort(key=lambda r: (not r["test_requirement_met"], r["metrics"]["compliant_error_rate"], -r["metrics"]["recall"], r["group"]))
            else:
                rows.sort(key=lambda r: (-r["metrics"]["balanced_accuracy"], r["group"]))
            for rank, row in enumerate(rows, 1):
                row["rank"] = rank
            profiles[profile] = dict(rows=rows, gaps=gaps)
        draws = bootstrap(meta, all_predictions)
        for profile, view in profiles.items():
            for row in view["rows"]:
                row["ci95"] = {k: interval(v) for k, v in draws[row["key"]].items()}
        pairs = []
        rows = profiles["balanced"]["rows"]
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                pa, pb = all_predictions[a["key"]], all_predictions[b["key"]]
                pairs.append(dict(a=a["group"], b=b["group"],
                    balanced_accuracy_difference=a["metrics"]["balanced_accuracy"] - b["metrics"]["balanced_accuracy"],
                    ci95=interval(draws[a["key"]]["balanced_accuracy"] - draws[b["key"]]["balanced_accuracy"]),
                    cases_fixed=int(((pa == y) & (pb != y)).sum()), cases_broken=int(((pa != y) & (pb == y)).sum())))
        result["datasets"][dataset] = dict(n=len(meta), positives=sum(y), negatives=len(y) - sum(y),
            duplicate_groups=len({r["group"] for r in meta}), profiles=profiles, paired_comparisons=pairs,
            uncertainty="2,000 paired duplicate-group bootstrap draws; descriptive, unadjusted; excludes search/inference uncertainty")
        print(f"Scored {dataset}: {len(rows)} balanced entries, {len(pairs)} paired comparisons", flush=True)
    return result


def evaluate(root, bundle):
    root, bundle = Path(root).resolve(), Path(bundle).resolve()
    check_freeze(bundle, root)
    if (bundle / "results.json").exists():
        raise ValueError("Test results already exist; reproduce instead of overwriting")
    archive = Archive(root)
    archive.specs = read(bundle / "registry.json")
    for dataset in DATASETS:
        values = {}
        for cid, spec in archive.specs.items():
            if spec["dataset"] == dataset:
                values[cid] = archive.values(spec, "test")
                archive.verify_test_replay(spec, values[cid])
        write(bundle / "test" / f"{dataset}.json.gz", dict(metadata=archive.metadata[dataset]["test"], candidates=values))
    write(bundle / "replay-verification.json", dict(fitted_candidates=archive.replay, all_matched=True))
    result = score_bundle(bundle)
    write(bundle / "results.json", result)
    exports(bundle, result)
    print("No API requests, GPU rentals, new language-model inference, or new fitting.", flush=True)


def exports(bundle, results):
    fields = ["dataset", "profile", "rank", "label", "category", "balanced_accuracy", "balanced_ci_low", "balanced_ci_high",
              "accuracy", "macro_f1", "mcc", "recall", "specificity", "precision", "false_positive_rate", "false_negative_rate",
              "false_blocks", "missed_violations", "unresolved", "coverage", "auroc", "average_precision", "score_coverage",
              "threshold", "test_requirement_met", "policy", "candidate", "candidate_count", "validation_rows", "fitting_rows"]
    with open(bundle / "leaderboard.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for dataset, d in results["datasets"].items():
            for profile, view in d["profiles"].items():
                for r in view["rows"]:
                    row = {k: r.get(k, r["metrics"].get(k)) for k in fields}
                    row.update(dataset=dataset, profile=profile, balanced_ci_low=r["ci95"]["balanced_accuracy"][0], balanced_ci_high=r["ci95"]["balanced_accuracy"][1])
                    writer.writerow(row)
    lines = ["# Balanced moderation leaderboard", "", "Retrospective reanalysis of saved outputs. Choices were selected on the common validation set, then frozen before this analysis scored the already-observed official tests. No new inference or fitting. The tables rank configured systems, not architectures in isolation.", ""]
    for dataset, d in results["datasets"].items():
        lines += [f"## {dataset}: {d['n']:,} test examples", "", f"{d['positives']:,} BLOCK; {d['negatives']:,} ALLOW. Balanced accuracy gives both classes equal weight.", ""]
        for profile, view in d["profiles"].items():
            lines += [f"### {PROFILE_NAMES[profile]}", "", "| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |", "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
            for r in view["rows"]:
                m, ci = r["metrics"], r["ci95"]["balanced_accuracy"]
                mcc = "—" if m["mcc"] is None else f"{m['mcc']:.3f}"
                target = "—" if profile == "balanced" else "Yes" if r["test_requirement_met"] else "No"
                lines.append(f"| {r['label']} | {m['balanced_accuracy']:.2%} ({ci[0]:.2%}–{ci[1]:.2%}) | {m['macro_f1']:.2%} | {mcc} | {m['recall']:.2%} | {m['false_positive_rate']:.2%} | {m['false_blocks']} / {m['missed_violations']} | {m['accuracy']:.2%} | {target} |")
            for gap in view["gaps"]:
                lines += ["", f"Not eligible on validation: `{gap['group']}` — {gap['reason']}."]
            lines += [""]
        lines += ["### Selected balanced configurations", "", "| Entry | Policy / policies | Decision rule | Archived candidates considered |", "|---|---|---|---:|"]
        for r in d["profiles"]["balanced"]["rows"]:
            decision = "Native / original archived decision" if r["threshold"] is None else f"BLOCK at score ≥ {r['threshold']:.2f}"
            lines.append(f"| {r['label']} | `{r['policy']}` | {decision} | {r['candidate_count']} |")
        lines += [""]
    lines += ["## Interpretation limits", "", "The same validation population was used within each benchmark, but earlier policy searches and fitting budgets differed. Some saved policies were tested only because earlier accuracy-based selection favored them; the candidate pool is therefore incomplete. Native categorical models have no score threshold. Ensembles retain previously fitted parameters and their original component policies. Reusing public tests makes this an exploratory comparison, not independent confirmation.", "", "Confidence intervals are unadjusted duplicate-group bootstrap intervals conditional on these saved outputs. Pairwise differences are in results.json. Rank order alone does not establish superiority. Unresolved outputs count as errors in accuracy and class recalls; MCC is omitted when unresolved outputs occur. AUROC and average precision in the CSV use genuine available scores and expose score coverage.", "", "See PLAN.md, coverage.json, selection.json, registry.json, and the interactive index.html for objectives, missing evaluations, configuration provenance, and detailed error/slice results."]
    (bundle / "RESULTS.md").write_text("\n".join(lines) + "\n")


def reproduce(bundle):
    bundle = Path(bundle).resolve()
    check_freeze(bundle)
    # Recompute selection, so the proof is stronger than replaying chosen cutoffs.
    expected_selection = read(bundle / "selection.json")
    specs = read(bundle / "registry.json")
    for dataset in DATASETS:
        val = read(bundle / "validation" / f"{dataset}.json.gz")
        y = [int(r["expected"] == "BLOCK") for r in val["metadata"]]
        grouped = defaultdict(dict)
        for cid, values in val["candidates"].items():
            grouped[specs[cid]["group"]][cid] = values
        for group, values in grouped.items():
            actual, _ = select(y, values)
            if actual != expected_selection[dataset][group]["choices"]:
                raise ValueError("Validation selection did not reproduce")
    result = score_bundle(bundle)
    if result != read(bundle / "results.json"):
        raise ValueError("Results did not reproduce exactly")
    print("PASS: validation selection, test metrics, slices, confidence intervals, and paired comparisons reproduce exactly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "evaluate", "reproduce"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.repo, args.bundle)
    elif args.command == "evaluate":
        evaluate(args.repo, args.bundle)
    else:
        reproduce(args.bundle)
