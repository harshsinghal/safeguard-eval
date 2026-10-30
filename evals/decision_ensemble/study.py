"""Prepare, fit/freeze, evaluate, and reproduce a saved-score experiment on CPU."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import platform
import shutil

import joblib
import numpy as np
import scipy
import sklearn
from sklearn.metrics import log_loss

from evals.decision_ensemble.learn import EPSILON, choose, describe, fit_candidates, values
from evals.ensemble.common import align, assert_disjoint
from evals.leaderboard.metrics import PROFILES, bootstrap, decisions, eligible, interval, metrics, select

ROOT = Path(__file__).resolve().parents[2]
MODELS = ("jev", "kev", "clef")
COHORTS = {"all-three": MODELS, "open-only": ("kev", "clef")}
POLICIES = ("brief", "detailed")
COUNTS = {"fit": 1024, "validation": 512, "test": 1699}
LABELS = {"fit": {"ALLOW": 479, "BLOCK": 545},
          "validation": {"ALLOW": 238, "BLOCK": 274},
          "test": {"ALLOW": 945, "BLOCK": 754}}
ARCHIVES = {"jev": "published_runs/2026-10-29-jev",
            "kev": "published_runs/2026-10-29-decision-models",
            "clef": "published_runs/2026-10-29-decision-models"}
LEADERBOARD = "published_runs/2026-10-29-leaderboard-decision-models"
REFERENCE_GROUPS = ("jev", "kev", "clef", "wildguard", "cope", "qwen-27b",
                    "wildguard-specialists/logit-equal")
META_FIELDS = ("id", "expected", "group", "prompt_sha256", "source_index", "subcategory", "adversarial", "split")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    p = Path(path)
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes())


def write(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    p.write_bytes(gzip.compress(data, mtime=0) if p.suffix == ".gz" else data)


def rows(path):
    with gzip.open(path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def source_files():
    files = list((ROOT / "evals/decision_ensemble").glob("*.py"))
    files += [ROOT / p for p in ("evals/__init__.py", "evals/ensemble/__init__.py",
        "evals/ensemble/common.py", "evals/ensemble/learn.py", "evals/leaderboard/__init__.py",
        "evals/leaderboard/metrics.py", "docs/decision-ensemble/PLAN.md", "tests/test_decision_ensemble.py")]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)}


def original(model, split, policy):
    middle = "" if model == "jev" else model + "/"
    return f"{ARCHIVES[model]}/predictions/{middle}wildguard/{split}/{policy}.jsonl.gz"


def local_input(model, split, policy):
    return f"inputs/{model}/{split}/{policy}.jsonl.gz"


def normalize(rr, split):
    if len(rr) != COUNTS[split] or dict(Counter(r["expected"] for r in rr)) != LABELS[split]:
        raise ValueError("Unexpected population or label mapping: " + split)
    out = []
    for r in rr:
        if r.get("split") != split:
            raise ValueError("Incorrect split marker")
        if r["prediction"] not in ("ALLOW", "BLOCK", "ERROR"):
            raise ValueError("Unexpected native decision")
        if r["prediction"] != "ERROR":
            p = r.get("probabilities", {})
            if set(p) != {"ALLOW", "BLOCK"} or abs(p["BLOCK"] - r["score"]) > 1e-8 or abs(sum(p.values()) - 1) > 1e-5:
                raise ValueError("Native score is not the recorded BLOCK probability")
        out.append({**{k: r[k] for k in META_FIELDS if k in r},
                    "prediction": r["prediction"], "score": r["score"]})
    return out


def population(bundle, split, selected):
    rr = {m: normalize(rows(bundle / local_input(m, split, selected[m])), split) for m in MODELS}
    meta, x, y, valid = align(rr, MODELS)
    meta = [{k: r[k] for k in META_FIELDS if k in r} for r in meta]
    indexes = {m: {r["id"]: r for r in rr[m]} for m in MODELS}
    native = np.array([[{"ALLOW": 0, "BLOCK": 1, "ERROR": -1}[indexes[m][r["id"]]["prediction"]]
                        for m in MODELS] for r in meta])
    return meta, x, y, valid, native


def verify_hashes(base, mapping):
    for relative, expected in mapping.items():
        if digest(base / relative) != expected:
            raise ValueError("Changed registered artifact: " + relative)


def prepare(bundle):
    if bundle.exists():
        raise ValueError("Destination exists; use a fresh bundle")
    bundle.mkdir(parents=True)
    sources = source_files()
    for rel in sources:
        target = bundle / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    shutil.copy2(ROOT / "docs/decision-ensemble/PLAN.md", bundle / "PLAN.md")
    original_hashes, inputs, held = {}, {}, {}
    for model in MODELS:
        checks = read(ROOT / ARCHIVES[model] / "checksums.json")
        for split in COUNTS:
            for policy in POLICIES:
                rel = original(model, split, policy)
                sha = digest(ROOT / rel)
                archive_rel = str(Path(rel).relative_to(ARCHIVES[model]))
                if checks[archive_rel] != sha:
                    raise ValueError("Archived source checksum mismatch: " + rel)
                original_hashes[rel] = sha
                target = local_input(model, split, policy)
                if split == "test":
                    # Hash raw bytes only; do not load test scores during preparation.
                    held[target] = dict(source=rel, sha256=sha)
                else:
                    (bundle / target).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / rel, bundle / target)
                    inputs[target] = sha
    policies = "published_runs/2026-10-29-jev/policies/wildguard/initial.json"
    shutil.copy2(ROOT / policies, bundle / "policies.json")
    original_hashes[policies] = digest(ROOT / policies)
    inputs["policies.json"] = digest(bundle / "policies.json")
    # Audit both complete-policy populations without using test examples.
    data_summary = {}
    for policy in POLICIES:
        fit = population(bundle, "fit", {m: policy for m in MODELS})
        val = population(bundle, "validation", {m: policy for m in MODELS})
        assert_disjoint(fit[0], val[0])
        data_summary[policy] = {}
        for split, data in (("fit", fit), ("validation", val)):
            meta, x, y, valid, native = data
            data_summary[policy][split] = dict(n=len(meta), labels=dict(Counter(r["expected"] for r in meta)),
                groups=len({r["group"] for r in meta}), unresolved=int((~valid).sum()),
                score_ranges={m: [float(x[valid[:, j], j].min()), float(x[valid[:, j], j].max())]
                              for j, m in enumerate(MODELS)})
    old = read(ROOT / LEADERBOARD / "selection.json")["wildguard"]
    registry = read(ROOT / LEADERBOARD / "registry.json")
    references = {g: dict(choice=old[g]["choices"]["balanced"],
        spec=registry[old[g]["choices"]["balanced"]["candidate"]]) for g in REFERENCE_GROUPS}
    write(bundle / "reference-selections.json", references)
    inputs["reference-selections.json"] = digest(bundle / "reference-selections.json")
    ref_test = LEADERBOARD + "/test/wildguard.json.gz"
    original_hashes[ref_test] = digest(ROOT / ref_test)
    original_hashes[LEADERBOARD + "/selection.json"] = digest(ROOT / LEADERBOARD / "selection.json")
    original_hashes[LEADERBOARD + "/registry.json"] = digest(ROOT / LEADERBOARD / "registry.json")
    registrations = {name: read(ROOT / path / "registration.json") for name, path in
                     (("jev", ARCHIVES["jev"]), ("open", ARCHIVES["kev"]))}
    prior_billing = read(ROOT / ARCHIVES["kev"] / "billing.json")
    write(bundle / "registration.json", dict(created_utc=now(), protocol_sha256=digest(bundle / "PLAN.md"),
        source_hashes=sources, original_hashes=original_hashes, development_hashes=inputs,
        held_out_sources=held, reference_test=ref_test, data_summary=data_summary,
        models=dict(jev=registrations["jev"]["resolved_model"], **registrations["open"]["models"]),
        no_new_inference=True, no_new_policy_text=True, counts=COUNTS,
        environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                         sklearn=sklearn.__version__, joblib=joblib.__version__),
        cost=dict(added_provider_cost_usd=0, cumulative_cost_usd=prior_billing["cumulative_cost_usd"],
                  cumulative_cap_usd=prior_billing["cumulative_cap_usd"], resources_started=0)))
    (bundle / "requirements.txt").write_text(f"numpy=={np.__version__}\nscipy=={scipy.__version__}\nscikit-learn=={sklearn.__version__}\njoblib=={joblib.__version__}\n")
    print("Prepared 12 development score files; test scores remain unloaded.", flush=True)


def policy_selection(bundle):
    choices = {}
    for model in MODELS:
        rr = {p: normalize(rows(bundle / local_input(model, "validation", p)), "validation") for p in POLICIES}
        meta, x, y, valid = align(rr, POLICIES)
        native = {p: {r["id"]: r["prediction"] for r in rr[p]} for p in POLICIES}
        candidates = {p: dict(score=[float(v) if ok else None for v, ok in zip(x[:, j], valid[:, j])],
            prediction=[{"ALLOW": 0, "BLOCK": 1, "ERROR": -1}[native[p][r["id"]]] for r in meta]) for j, p in enumerate(POLICIES)}
        selected, grid = select(y, candidates)
        choices[model] = dict(policy=selected["balanced"]["candidate"],
                              choice=selected["balanced"], grid=grid)
    return choices


def fitting(bundle):
    policies = policy_selection(bundle)
    chosen = {m: policies[m]["policy"] for m in MODELS}
    tm, x, y, valid, native = population(bundle, "fit", chosen)
    vm, v, vy, vv, vn = population(bundle, "validation", chosen)
    assert_disjoint(tm, vm)
    fitted, all_selections, all_outputs, grids, descriptions, diagnostics = {}, {}, {}, {}, {}, {}
    for cohort, names in COHORTS.items():
        cols = [MODELS.index(m) for m in names]
        candidates, diag = fit_candidates(list(names), x[:, cols], y, valid[:, cols],
                                         native[:, cols], np.array([r["group"] for r in tm]))
        selections, outputs, grid = choose(list(names), candidates, vy, v[:, cols], vv[:, cols], vn[:, cols])
        fitted[cohort] = candidates
        all_selections[cohort], all_outputs[cohort], grids[cohort] = selections, outputs, grid
        descriptions[cohort], diagnostics[cohort] = describe(candidates), diag
    return dict(policies=policies, chosen=chosen, fitted=fitted, selections=all_selections,
                outputs=all_outputs, grids=grids, parameters=descriptions, diagnostics=diagnostics)


def fit(bundle):
    if (bundle / "freeze.json").exists():
        raise ValueError("Already frozen; reproduce rather than replacing selections")
    registration = read(bundle / "registration.json")
    verify_hashes(bundle, registration["development_hashes"])
    verify_hashes(ROOT, registration["source_hashes"])
    result = fitting(bundle)
    write(bundle / "policy-selection.json", result["policies"])
    write(bundle / "selection.json", result["selections"])
    write(bundle / "validation-outputs.json.gz", result["outputs"])
    write(bundle / "validation-grid.json.gz", result["grids"])
    write(bundle / "parameters.json", result["parameters"])
    write(bundle / "fitting-diagnostics.json", result["diagnostics"])
    joblib.dump(result["fitted"], bundle / "models.joblib", compress=3)
    artifacts = {str(p.relative_to(bundle)): digest(p) for p in bundle.rglob("*") if p.is_file()}
    write(bundle / "freeze.json", dict(created_utc=now(), status="frozen before extension test evaluation",
        protocol_sha256=registration["protocol_sha256"], artifact_hashes=artifacts,
        policies=result["chosen"], primary="all-three/probability-logistic", primary_profile="balanced",
        expected_test_n=1699, caveat="Previously examined public test; exploratory reused-score study"))
    print("Frozen policies:", result["chosen"], flush=True)
    for cohort in COHORTS:
        s = result["selections"][cohort]
        print(cohort, "primary:", s["probability-logistic"]["balanced"], flush=True)
        print(cohort, "best individual:", s["single"]["balanced"]["candidate"],
              "; best score ensemble:", s["best-score-ensemble"]["balanced"]["candidate"], flush=True)


def check_freeze(bundle):
    freeze = read(bundle / "freeze.json")
    verify_hashes(bundle, freeze["artifact_hashes"])
    verify_hashes(ROOT, read(bundle / "registration.json")["source_hashes"])
    return freeze


def extra_metrics(y, predicted, scores):
    m = metrics(y, predicted, scores)
    if scores is not None:
        ss = np.array([np.nan if s is None else s for s in scores])
        good = np.isfinite(ss) & (np.asarray(predicted) != -1)
        if good.any():
            m["brier"] = float(np.mean((ss[good] - y[good]) ** 2))
            m["log_loss"] = float(log_loss(y[good], ss[good], labels=[0, 1]))
    return m


def ref_values(meta, ref_test, candidate):
    reference = {r["id"]: (i, r) for i, r in enumerate(ref_test["metadata"])}
    if len(reference) != len(ref_test["metadata"]) or set(reference) != {r["id"] for r in meta}:
        raise ValueError("Historical reference population mismatch")
    indexes = []
    for r in meta:
        i, other = reference[r["id"]]
        if any(other[k] != r[k] for k in ("expected", "group", "prompt_sha256")):
            raise ValueError("Historical reference label, group, or content mismatch")
        indexes.append(i)
    value = ref_test["candidates"][candidate]
    return {k: None if v is None else [v[i] for i in indexes] for k, v in value.items() if k in ("score", "prediction")}


def score(bundle, fitted):
    freeze = check_freeze(bundle)
    meta, x, y, valid, native = population(bundle, "test", freeze["policies"])
    tm = population(bundle, "fit", freeze["policies"])[0]
    vm = population(bundle, "validation", freeze["policies"])[0]
    assert_disjoint(tm, vm, meta)
    selections = read(bundle / "selection.json")
    result_rows, predictions, raw_outputs, candidate_results = {}, {}, {}, {}
    for cohort, names in COHORTS.items():
        cols = [MODELS.index(m) for m in names]
        outputs = {c["id"]: values(c, x[:, cols], valid[:, cols], native[:, cols]) for c in fitted[cohort]}
        raw_outputs[cohort] = outputs
        # Every registered candidate's native result is retained, never used to select.
        candidate_results[cohort] = {cid: extra_metrics(y, v["prediction"], v.get("score")) for cid, v in outputs.items()}
        for family, by_profile in selections[cohort].items():
            for profile, chosen in by_profile.items():
                key = f"{cohort}/{family}/{profile}"
                if chosen is None:
                    result_rows[key] = dict(eligible_on_validation=False, cohort=cohort, family=family, profile=profile)
                    continue
                v = outputs[chosen["candidate"]]
                p = decisions(v, chosen["threshold"])
                predictions[key] = p
                m = extra_metrics(y, p, v.get("score"))
                slices = {}
                for field in ("subcategory", "adversarial"):
                    slices[field] = {}
                    for value in sorted({str(r.get(field)) for r in meta}):
                        ix = [i for i, r in enumerate(meta) if str(r.get(field)) == value]
                        slices[field][value] = metrics(y[ix], p[ix])
                result_rows[key] = dict(eligible_on_validation=True, cohort=cohort, family=family,
                    profile=profile, candidate=chosen["candidate"], threshold=chosen["threshold"],
                    validation=chosen["metrics"], metrics=m, test_requirement_met=eligible(m, profile), slices=slices)
    references = read(bundle / "reference-selections.json")
    reference_values = read(bundle / "reference-test.json.gz")
    for group, ref in references.items():
        chosen, v = ref["choice"], reference_values[group]
        p = decisions(v, chosen["threshold"])
        key = "reference/" + group
        predictions[key] = p
        result_rows[key] = dict(eligible_on_validation=True, historical_reference=True,
            candidate=chosen["candidate"], threshold=chosen["threshold"], policy=ref["spec"]["policy"],
            metrics=extra_metrics(y, p, v.get("score")), label=ref["spec"]["label"])
    draws = bootstrap(meta, predictions)
    for key, p in predictions.items():
        result_rows[key]["ci95"] = {m: interval(d) for m, d in draws[key].items()}
    primary = "all-three/probability-logistic/balanced"
    pairs = [(primary, "all-three/single/balanced"), (primary, "reference/wildguard"),
             (primary, "all-three/decision-logistic/balanced"), (primary, "all-three/majority/balanced"),
             ("open-only/probability-logistic/balanced", "open-only/single/balanced"),
             ("open-only/probability-logistic/balanced", primary),
             ("all-three/best-score-ensemble/balanced", "all-three/single/balanced")]
    pairs += [(primary, "reference/" + g) for g in REFERENCE_GROUPS if g != "wildguard"]
    paired = []
    for a, b in pairs:
        ma, mb = result_rows[a]["metrics"], result_rows[b]["metrics"]
        paired.append(dict(a=a, b=b, balanced_accuracy_difference=ma["balanced_accuracy"] - mb["balanced_accuracy"],
            ci95=interval(draws[a]["balanced_accuracy"] - draws[b]["balanced_accuracy"]),
            cases_fixed=int(((predictions[a] == y) & (predictions[b] != y)).sum()),
            cases_broken=int(((predictions[a] != y) & (predictions[b] == y)).sum())))
    error = native != y[:, None]
    diagnostics = dict(score_correlation=np.corrcoef(x, rowvar=False).tolist(), model_order=list(MODELS),
        overlapping_native_errors={a + "/" + b: int((error[:, i] & error[:, j]).sum())
            for i, a in enumerate(MODELS) for j, b in enumerate(MODELS) if i < j},
        all_three_native_errors=int(error.all(axis=1).sum()),
        clipped_logodds_counts={m: int((valid[:, j] & ((x[:, j] < EPSILON) | (x[:, j] > 1 - EPSILON))).sum())
                               for j, m in enumerate(MODELS)})
    results = dict(primary=primary, n=len(meta), positives=int(y.sum()), negatives=int((1-y).sum()),
        duplicate_groups=len({r["group"] for r in meta}), rows=result_rows,
        paired_comparisons=paired, diagnostics=diagnostics, candidate_native_metrics=candidate_results,
        uncertainty="2,000 paired group-bootstrap draws; unadjusted; reused tests and unequal development histories",
        cost=read(bundle / "registration.json")["cost"])
    return results, dict(metadata=meta, candidates=raw_outputs,
                         selected_predictions={k: v.tolist() for k, v in predictions.items()})


def evaluate(bundle):
    if (bundle / "results.json").exists():
        raise ValueError("Results already exist; use reproduce")
    freeze = check_freeze(bundle)
    reg = read(bundle / "registration.json")
    verify_hashes(ROOT, reg["original_hashes"])
    for target, spec in reg["held_out_sources"].items():
        path = bundle / target
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / spec["source"], path)
    meta = population(bundle, "test", freeze["policies"])[0]
    refs = read(bundle / "reference-selections.json")
    previous = read(ROOT / reg["reference_test"])
    write(bundle / "reference-test.json.gz", {g: ref_values(meta, previous, ref["choice"]["candidate"]) for g, ref in refs.items()})
    fitted = joblib.load(bundle / "models.joblib")  # Own hash-verified locally produced artifact.
    results, predictions = score(bundle, fitted)
    write(bundle / "results.json", results)
    write(bundle / "test-predictions.json.gz", predictions)
    write(bundle / "evaluation.json", dict(created_utc=now(), freeze_sha256=digest(bundle / "freeze.json"),
        test_input_hashes={target: digest(bundle / target) for target in reg["held_out_sources"]},
        reference_test_sha256=digest(bundle / "reference-test.json.gz")))
    print("Evaluated all frozen methods on 1,699 prompts. Added GPU/API spend: $0.", flush=True)


def assert_close(a, b, path="root"):
    if isinstance(a, dict):
        if set(a) != set(b): raise ValueError("Reproduction keys differ: " + path)
        for key in a: assert_close(a[key], b[key], path + "/" + key)
    elif isinstance(a, list):
        if len(a) != len(b): raise ValueError("Reproduction length differs: " + path)
        for i, (x, y) in enumerate(zip(a, b)): assert_close(x, y, path + f"/{i}")
    elif isinstance(a, (float, int)) and not isinstance(a, bool):
        if not np.isclose(a, b, atol=1e-10, rtol=1e-10): raise ValueError("Reproduction number differs: " + path)
    elif a != b:
        raise ValueError("Reproduction value differs: " + path)


def reproduce(bundle):
    check_freeze(bundle)
    evaluation = read(bundle / "evaluation.json")
    verify_hashes(bundle, evaluation["test_input_hashes"])
    if digest(bundle / "reference-test.json.gz") != evaluation["reference_test_sha256"]:
        raise ValueError("Reference test changed")
    if (bundle / "checksums.json").exists():
        verify_hashes(bundle, read(bundle / "checksums.json"))
    fresh = fitting(bundle)
    for key, path in (("policies", "policy-selection.json"), ("selections", "selection.json"),
                      ("outputs", "validation-outputs.json.gz"), ("parameters", "parameters.json"),
                      ("grids", "validation-grid.json.gz"), ("diagnostics", "fitting-diagnostics.json")):
        assert_close(fresh[key], read(bundle / path))
    results, predictions = score(bundle, fresh["fitted"])
    assert_close(results, read(bundle / "results.json"))
    assert_close(predictions, read(bundle / "test-predictions.json.gz"))
    write(bundle / "reproduction.json", dict(created_utc=now(), policies_matched=True,
        refitted_models_matched=True, validation_selections_matched=True, test_outputs_matched=True,
        metrics_and_intervals_matched=True, added_provider_cost_usd=0))
    print("Reproduced policy selections, fresh fits, validation choices, test scores, metrics, and intervals.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "fit", "evaluate", "reproduce"))
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    globals()[args.command](args.bundle.resolve())


if __name__ == "__main__":
    main()
