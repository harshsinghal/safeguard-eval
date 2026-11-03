"""Integrate two published studies without refitting or changing their selections.

This is an evidence-publication operation, not a fresh experiment or test holdout.
All old entries survive unchanged; new entries retain their original validation
choices. Selection aliases and individual calibration controls are not new rows.
"""
import argparse
import copy
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from evals.leaderboard.archive import digest, read, read_rows, write
from evals.leaderboard.build import exports, now, score_bundle
from evals.leaderboard.metrics import select
from evals.leaderboard.render import render

PRIOR = "2026-10-29-leaderboard-decision-models"
STUDY = "2026-10-30-decision-ensemble"
FAMILIES = {
    "probability-logistic": "Logistic regression · probabilities",
    "logodds-logistic": "Logistic regression · log-odds",
    "equal-probability": "Equal probability average",
    "equal-calibrated": "Calibrated probability average",
    "equal-logodds": "Equal log-odds average",
    "weighted": "Learned weighted average",
    "forest": "Random forest",
    "decision-logistic": "Logistic regression · decisions only",
    "majority": "Majority vote · decisions only",
}
COHORTS = {"all-three": ["jev", "kev", "clef"], "open-only": ["kev", "clef"]}
MODEL_IDS = {"jev": "typesafe/jev-1.14-20261014", "kev": "jaredpalmer/kev-4b",
             "clef": "Cloudflare/clef-flash"}


def verify_bundle(bundle):
    manifest = read(bundle / "checksums.json")
    for relative, expected in manifest.get("sha256", manifest).items():
        if digest(bundle / relative) != expected:
            raise ValueError("Changed source evidence: " + str(bundle / relative))


def require_same_order(reference, incoming):
    """Predictions are positional; equality of sets alone would permit corruption."""
    fields = ("id", "expected", "group", "prompt_sha256", "subcategory", "adversarial")
    if len(reference) != len(incoming) or len({r["id"] for r in incoming}) != len(incoming):
        raise ValueError("Population size or duplicate IDs differ")
    for left, right in zip(reference, incoming):
        if any(left.get(k) != right.get(k) for k in fields):
            raise ValueError("Population or ordering mismatch at " + left["id"])


def mapped_choices(choices, prefix):
    result = copy.deepcopy(choices)
    for chosen in result.values():
        if chosen is not None:
            chosen["candidate"] = prefix + chosen["candidate"]
    return result


def verify_results(prior, study, current):
    """Publishing together must not change a single earlier result or choice."""
    checked = 0
    for dataset, old_data in prior["datasets"].items():
        for profile, old_view in old_data["profiles"].items():
            view = current["datasets"][dataset]["profiles"][profile]
            rows = {r["group"]: r for r in view["rows"]}
            for old in old_view["rows"]:
                strip_rank = lambda r: {k: v for k, v in r.items() if k != "rank"}
                if strip_rank(old) != strip_rank(rows[old["group"]]):
                    raise ValueError("Changed previous result: " + old["key"])
                checked += 1
            old_groups = {g["group"] for g in old_view["gaps"]}
            if not old_groups <= {g["group"] for g in view["gaps"]}:
                raise ValueError("Changed previous eligibility")
    added = 0
    for profile, view in current["datasets"]["wildguard"]["profiles"].items():
        for row in view["rows"]:
            if not row["group"].startswith("decision-ensemble/"):
                continue
            _, cohort, family = row["group"].split("/")
            source = study["rows"][f"{cohort}/{family}/{profile}"]
            # The source study also reports calibration losses; the common
            # leaderboard reports classification and ranking metrics only.
            shared_metrics = {k: v for k, v in source["metrics"].items() if k not in ("brier", "log_loss")}
            if row["metrics"] != shared_metrics or row["threshold"] != source["threshold"]:
                raise ValueError("Changed experiment result: " + row["key"])
            if row["validation"] != source["validation"]:
                raise ValueError("Changed experiment validation result")
            added += 1
    return dict(previous_profile_rows_unchanged=checked, added_profile_rows_match_study=added)


def extend(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError("Use a new destination; published evidence must not be overwritten")
    prior, study = root / "published_runs" / PRIOR, root / "published_runs" / STUDY
    verify_bundle(prior)
    verify_bundle(study)
    destination.mkdir(parents=True)
    registry = read(prior / "registry.json")
    selection = read(prior / "selection.json")
    grids = {}
    coverage = read(prior / "coverage.json")
    development = {d: read(prior / "validation" / f"{d}.json.gz") for d in selection}
    test = {d: read(prior / "test" / f"{d}.json.gz") for d in selection}
    for dataset, data in development.items():
        grouped = defaultdict(dict)
        for cid, value in data["candidates"].items():
            grouped[registry[cid]["group"]][cid] = value
        grids[dataset] = {}
        for group, values in grouped.items():
            choices, grid = select([int(r["expected"] == "BLOCK") for r in data["metadata"]], values)
            if choices != selection[dataset][group]["choices"]:
                raise ValueError("Previous validation selection did not reproduce: " + group)
            grids[dataset][group] = grid
    incoming_val = read(study / "validation-outputs.json.gz")
    incoming_test = read(study / "test-predictions.json.gz")
    val_meta = sorted(read_rows(study / "inputs/jev/validation/detailed.jsonl.gz"), key=lambda r: r["id"])
    require_same_order(development["wildguard"]["metadata"], val_meta)
    require_same_order(test["wildguard"]["metadata"], incoming_test["metadata"])
    source_selection, parameters = read(study / "selection.json"), read(study / "parameters.json")
    policies = read(study / "freeze.json")["policies"]
    labels = [int(r["expected"] == "BLOCK") for r in val_meta]
    for cohort, members in COHORTS.items():
        prefix = f"wildguard/decision-ensemble/{cohort}/"
        suffix = "Jev + Kev + Clef" if cohort == "all-three" else "Kev + Clef (open weights)"
        for family, title in FAMILIES.items():
            group = f"decision-ensemble/{cohort}/{family}"
            candidates = {}
            for cid, parameter in parameters[cohort].items():
                if parameter["family"] != family:
                    continue
                identifier = prefix + cid
                candidates[identifier] = incoming_val[cohort][cid]
                registry[identifier] = dict(id=identifier, dataset="wildguard", group=group,
                    label=title + " · " + suffix, category="Ensemble",
                    model_id=" + ".join(MODEL_IDS[m] for m in members),
                    policy="; ".join(f"{m}:{policies[m]}" for m in members),
                    adapter="Native decisions" if family in ("decision-logistic", "majority") else "Native BLOCK scores",
                    source_archive=STUDY, source_candidate=cid, source_cohort=cohort,
                    kind="normalized-published-output", fitting_rows=1024, validation_rows=512)
                development["wildguard"]["candidates"][identifier] = incoming_val[cohort][cid]
                test["wildguard"]["candidates"][identifier] = incoming_test["candidates"][cohort][cid]
            actual, grid = select(labels, candidates)
            expected = mapped_choices(source_selection[cohort][family], prefix)
            if actual != expected:
                raise ValueError("Source validation selection did not reproduce: " + group)
            selection["wildguard"][group] = dict(choices=expected, candidates=len(candidates))
            grids["wildguard"][group] = grid
    coverage["candidate_counts"] = dict(Counter(s["dataset"] for s in registry.values()))
    coverage["decision_ensemble_extension"] = dict(
        source=STUDY, added_candidate_records=52, added_entries=18,
        cohorts=COHORTS, hatexplain="not evaluated for these decision ensembles",
        note="Seven score-combiner families and two decision-only controls per cohort. Selection aliases are not entries. Individual calibration controls remain in the source study; previous individual entries are unchanged.")
    coverage["historical_results"]["decision-ensemble"] = f"published_runs/{STUDY}/README.md"
    for name, value in (("registry.json", registry), ("selection.json", selection),
                        ("coverage.json", coverage), ("validation-grid.json.gz", grids)):
        write(destination / name, value)
    for dataset in selection:
        write(destination / "validation" / f"{dataset}.json.gz", development[dataset])
        write(destination / "test" / f"{dataset}.json.gz", test[dataset])
    frozen = ["registry.json", "selection.json", "coverage.json", "validation-grid.json.gz"]
    frozen += [f"{split}/{d}.json.gz" for split in ("validation", "test") for d in selection]
    write(destination / "freeze.json", dict(created_utc=now(),
        status="published selections copied unchanged; not a new pre-test experiment",
        analysis_role="retrospective integration of published results; public tests reused",
        primary="balanced_accuracy", expected_test_n={d: len(test[d]["metadata"]) for d in selection},
        artifact_hashes={p: digest(destination / p) for p in frozen},
        input_hashes={f"published_runs/{p.name}/checksums.json": digest(p / "checksums.json") for p in (prior, study)},
        no_new_inference=True, no_new_fitting=True, cost_usd=0,
        note="Prior individual candidates remain unchanged, including their policy pools. New study controls are not substituted after observing test results."))
    results = score_bundle(destination)
    verification = verify_results(read(prior / "results.json"), read(study / "results.json"), results)
    write(destination / "results.json", results)
    write(destination / "extension-provenance.json", dict(prior=PRIOR, experiment=STUDY,
        previous_entries_unchanged=True, source_selection_unchanged=True, **verification))
    exports(destination, results)
    render(destination)
    shutil.copytree(prior / "source", destination / "source")
    for path in (root / "evals/leaderboard").glob("*.py"):
        shutil.copy2(path, destination / "source/evals/leaderboard" / path.name)
    print("Integrated 38 WildGuard and 20 HateXplain entries from 261 candidate records. No inference or fitting.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()
    extend(args.repo, args.bundle)
