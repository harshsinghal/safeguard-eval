"""Readable, fixed-order report of registered methods; no selection or fitting."""
import argparse
import csv
from pathlib import Path

from evals.decision_ensemble.study import read

LABELS = {"probability-logistic": "Probability logistic — primary",
          "logodds-logistic": "Log-odds logistic", "equal-probability": "Equal probability average",
          "equal-calibrated": "Equal calibrated average", "equal-logodds": "Equal log-odds average",
          "weighted": "Learned weighted average", "forest": "Random forest",
          "decision-logistic": "Decision-only logistic", "majority": "Fixed majority vote",
          "single": "Validation-selected best individual", "single-jev": "Jev: selected individual",
          "single-kev": "Kev: selected individual", "single-clef": "Clef: selected individual",
          "best-score-ensemble": "Validation-selected best score ensemble"}
ORDER = tuple(LABELS)


def render(bundle):
    data = read(bundle / "results.json")
    frozen = read(bundle / "freeze.json")
    policies = read(bundle / "policy-selection.json")
    parameters = read(bundle / "parameters.json")
    lines = ["# WildGuard decision-score ensemble results", "",
        "Exploratory October 30, 2026 follow-up using saved native BLOCK probabilities. "
        "All new fitting used 1,024 training prompts; policy, hyperparameter and cutoff selection used 512 separate validation prompts. "
        "The 1,699 test prompts were held out of those operations but had been examined in earlier studies.", "",
        "## Frozen input policies", "", "| Model | Selected policy | Raw validation balanced accuracy |", "|---|---|---:|"]
    for model, p in policies.items():
        lines.append(f"| {model} | {p['policy']} | {p['choice']['metrics']['balanced_accuracy']:.2%} |")
    lines += ["", "Brief and detailed were the eligible policy pool. Example-bearing policies lack saved fitting scores and were excluded from new ensemble inputs. Their earlier selected individual results remain historical references below.", ""]
    rows = []
    for cohort, title in (("all-three", "Jev + Kev + Clef"), ("open-only", "Open weights only: Kev + Clef")):
        lines += [f"## {title}", "",
            "Methods appear in registered order, not in a ranking selected from test results. 'Best' refers to validation selection.", "",
            "| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | Catch rate | False-block rate | False blocks / missed | Unresolved |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for family in ORDER:
            key = f"{cohort}/{family}/balanced"
            if key not in data["rows"]: continue
            row = data["rows"][key]
            if not row["eligible_on_validation"]: continue
            m, ci = row["metrics"], row["ci95"]["balanced_accuracy"]
            lines.append(f"| {LABELS[family]} | {m['balanced_accuracy']:.2%} ({ci[0]:.2%}–{ci[1]:.2%}) | {m['accuracy']:.2%} | {m['macro_f1']:.2%} | {m['recall']:.2%} | {m['false_positive_rate']:.2%} | {m['false_blocks']} / {m['missed_violations']} | {m['unresolved']} |")
            rows.append(dict(key=key, label=LABELS[family], **row))
        lines += ["", "### Selected settings", "", "| Method | Candidate | BLOCK cutoff | Validation balanced accuracy |", "|---|---|---:|---:|"]
        for row in rows:
            if row["cohort"] != cohort: continue
            t = "native / fixed" if row["threshold"] is None else f"{row['threshold']:.2f}"
            lines.append(f"| {row['label']} | `{row['candidate']}` | {t} | {row['validation']['balanced_accuracy']:.2%} |")
        lines += ["", "### Primary score equation", ""]
        primary = data["rows"][f"{cohort}/probability-logistic/balanced"]
        linear = parameters[cohort][primary["candidate"]]["linear_parameters"]
        names = ["jev", "kev", "clef"] if cohort == "all-three" else ["kev", "clef"]
        equation = f"{linear['intercept']:.6f}" + "".join(f" {c:+.6f} × p_{m}" for m, c in zip(names, linear["coefficients"]))
        lines += ["```text", f"ensemble_score = sigmoid({equation})", "```", "",
            "Here p_model is the saved native BLOCK probability under that model's selected policy. "
            "Coefficients include the fitting-only standardization in the equation above. They are fitted coefficients, not causal importance scores. "
            "The score is not assumed to be a calibrated probability for production traffic.", ""]
    lines += ["## Historical references", "",
        "These retain their earlier balanced-validation selections, which used different policy pools and fitting histories. "
        "None is an input to the new ensemble unless it is one of the explicitly named decision-model components above.", "",
        "| Reference | Balanced accuracy | Accuracy | False blocks / missed |", "|---|---:|---:|---:|"]
    for key, row in data["rows"].items():
        if not key.startswith("reference/"): continue
        m = row["metrics"]
        lines.append(f"| {row['label']} | {m['balanced_accuracy']:.2%} | {m['accuracy']:.2%} | {m['false_blocks']} / {m['missed_violations']} |")
    lines += ["", "## Registered paired comparisons", "",
        "Differences below are balanced-accuracy percentage points, A minus B. "
        "The 2,000-draw group-bootstrap intervals are descriptive and unadjusted. "
        "An interval spanning zero does not resolve a clear difference.", "",
        "| A | B | Difference | 95% interval | Cases fixed / broken |", "|---|---|---:|---:|---:|"]
    for p in data["paired_comparisons"]:
        lo, hi = p["ci95"]
        lines.append(f"| `{p['a']}` | `{p['b']}` | {100*p['balanced_accuracy_difference']:+.2f} | {100*lo:+.2f} to {100*hi:+.2f} | {p['cases_fixed']} / {p['cases_broken']} |")
    lines += ["", "## Separately selected operational targets", "",
        "These use their own validation-selected settings, not the balanced cutoff. "
        "A validation target is not a test guarantee.", "",
        "| Cohort / method | Target | Catch rate | False-block rate | Test target met? |", "|---|---|---:|---:|---|"]
    for cohort in ("all-three", "open-only"):
        for family in ("probability-logistic", "single", "best-score-ensemble"):
            for profile in ("false_block_limit", "catch_target"):
                r = data["rows"][f"{cohort}/{family}/{profile}"]
                if not r["eligible_on_validation"]:
                    lines.append(f"| {cohort} / {family} | {profile} | — | — | No validation candidate |")
                else:
                    m = r["metrics"]
                    lines.append(f"| {cohort} / {family} | {profile} | {m['recall']:.2%} | {m['false_positive_rate']:.2%} | {'Yes' if r['test_requirement_met'] else 'No'} |")
    lines += ["", "## Evidence and limitations", "",
        "See `results.json` for all metrics, calibration diagnostics, category slices and paired comparisons; "
        "`parameters.json` for all fitted coefficients and averaging weights; `validation-grid.json.gz` for the full search; "
        "and `test-predictions.json.gz` for scores and frozen decisions. `PLAN.md`, `registration.json`, "
        "and `freeze.json` record the procedure and hashes.", "",
        "The selected component policies, score scales, clipping convention, validation objective and cohort all affect this comparison. "
        "Previously examined tests, repeated validation use, machine-versus-human annotation differences, incomplete upstream training disclosure "
        "and limited candidate pools prevent treating this as a performance ceiling or architecture verdict. "
        "Ensembles require two or three model evaluations per input; saved-score replay does not measure live serving latency or cost.", "",
        "Added GPU/API cost: $0. Small calibrators and combiners were trained on labels; no language-model weights were updated."]
    (bundle / "RESULTS.md").write_text("\n".join(lines) + "\n")
    fields = ("key", "cohort", "family", "profile", "candidate", "threshold", "balanced_accuracy",
              "accuracy", "macro_f1", "mcc", "recall", "specificity", "false_positive_rate", "false_negative_rate",
              "false_blocks", "missed_violations", "unresolved", "coverage", "auroc", "average_precision", "brier", "log_loss")
    with (bundle / "results.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key, row in data["rows"].items():
            if row["eligible_on_validation"]:
                flat = dict(key=key, **row, **row["metrics"])
                writer.writerow({k: flat.get(k) for k in fields})
    print("Wrote RESULTS.md and results.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    render(parser.parse_args().bundle.resolve())
