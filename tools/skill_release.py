#!/usr/bin/env python3
"""Refresh, check, and package the evidence-backed skill. No model calls or network."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "safeguard-eval"
SOURCES = {
    "interface-audit": "docs/research-directions/POLICY-INTERFACE-AUDIT.md",
    "shared-adapters": "evals/run.py",
    "wildguard-runner": "evals/wildguard/run.py",
    "qwen-runner": "evals/qwen_policy/run.py",
    "hatexplain-renderer": "evals/hatexplain/policy.py",
    "model-exposure": "docs/wildguard/MODEL_EXPOSURE.md",
    "wildguard-methods": "docs/wildguard/METHODS.md",
    "wildguard-data": "docs/wildguard/data-manifest.json",
    "wildguard-official-source": "docs/wildguard/official-source.json",
    "wildguard-results": "published_runs/2026-10-24-wildguard/README.md",
    "wildguard-claims": "docs/wildguard/CLAIMS.md",
    "wildguard-analysis": "published_runs/2026-10-24-wildguard/analysis.json",
    "qwen-results": "published_runs/2026-10-25-qwen/README.md",
    "qwen-edits": "docs/qwen-policy/PROMPT-CHANGES.md",
    "qwen-analysis": "published_runs/2026-10-25-qwen/analysis.json",
    "transfer-readout": "docs/policy-transfer/READOUT.md",
    "transfer-edits": "docs/policy-transfer/POLICY-CHANGES.md",
    "transfer-results": "published_runs/2026-10-25-policy-transfer/README.md",
    "transfer-analysis": "published_runs/2026-10-25-policy-transfer/analysis.json",
    "hatexplain-plan": "docs/hatexplain/PLAN.md",
    "hatexplain-data": "docs/hatexplain/data-manifest.json",
    "hatexplain-results": "published_runs/2026-10-26-hatexplain/README.md",
    "hatexplain-readout": "docs/hatexplain/READOUT.md",
    "hatexplain-edits": "docs/hatexplain/POLICY-CHANGES.md",
    "hatexplain-scope": "docs/hatexplain/SCOPE-REVIEW.md",
    "hatexplain-analysis": "published_runs/2026-10-26-hatexplain/analysis.json",
    "ensemble-readout": "docs/ensemble/READOUT.md",
    "ensemble-results": "docs/ensemble/RESULTS.md",
    "ensemble-archive": "published_runs/2026-10-27-ensemble/README.md",
    "ensemble-data": "docs/ensemble/data-manifest.json",
    "logits-claims": "docs/ensemble-logits/CLAIMS.md",
    "logits-results": "docs/ensemble-logits/RESULTS.md",
    "logits-plan": "docs/ensemble-logits/PLAN.md",
    "logits-wildguard": "published_runs/2026-10-28-ensemble-logits/cohorts/wildguard-specialists/results.json",
    "logits-hate-specialists": "published_runs/2026-10-28-ensemble-logits/cohorts/hatexplain-specialists/results.json",
    "logits-hate-mixed": "published_runs/2026-10-28-ensemble-logits/cohorts/hatexplain-mixed/results.json",
    "early-demo": "published_runs/2026-10-21/README.md",
    "demo-methods": "evals/README.md",
    "injection-results": "published_runs/2026-10-24-injection/README.md",
    "injection-methods": "evals/injection/README.md",
    "injection-provenance": "evals/injection/provenance.json",
    "frontier-pilot": "published_runs/2026-10-25-frontier-pilot/README.md",
    "enterprise-track": "docs/research-directions/ENTERPRISE-AI-GOVERNANCE.md",
    "paper-home": "research-preprint/README.md",
    "paper-pdf": "research-preprint/output/pdf/policy-as-interface-review-v0.5.pdf",
    "paper-text": "research-preprint/output/text/policy-as-interface-review-v0.5.txt",
    "paper-source": "research-preprint/output/policy-as-interface-source-v0.5.zip",
    "paper-publication": "research-preprint/publication.json",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registry(release: dict) -> dict:
    revision = release["evidence_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("evidence_revision must be a full commit SHA")
    sources = []
    for source_id, path in SOURCES.items():
        committed = git("show", f"{revision}:{path}")
        if (ROOT / path).read_bytes() != committed:
            raise ValueError(f"Evidence changed since the pinned revision: {path}. Review the skill and refresh its evidence pin.")
        repository = release["repository"]
        sources.append({"id": source_id, "path": path, "sha256": digest(committed),
                        "url": f"{repository}/blob/{revision}/{path}",
                        "raw_url": f"https://raw.githubusercontent.com/harshsinghal/safeguard-eval/{revision}/{path}"})
    recorded = git("ls-tree", "-d", "--name-only", f"{revision}:published_runs").decode().splitlines()
    recorded = sorted(x for x in recorded if re.match(r"\d{4}-", x))
    current = sorted(p.name for p in (ROOT / "published_runs").iterdir()
                     if p.is_dir() and re.match(r"\d{4}-", p.name))
    if current != recorded:
        raise ValueError("Published study inventory changed. Review new evidence and update the skill snapshot.")
    covered = {Path(p).parts[1] for p in SOURCES.values() if p.startswith("published_runs/")}
    # The first ensemble is cited through its readout; keep an explicit registry link too.
    if set(recorded) - covered:
        raise ValueError("Study directories without a source entry: " + ", ".join(sorted(set(recorded) - covered)))
    return {"evidence_revision": revision, "evidence_through": release["evidence_through"],
            "recorded_run_directories": recorded, "sources": sources}


def compact_metrics(metrics: dict) -> dict:
    keys = ("n", "accuracy", "macro_f1", "harmful_f1", "harmful_recall", "hate_f1",
            "hate_recall", "violation_f1", "violation_recall", "false_blocks",
            "missed_hate", "missed_violations", "errors", "confusion")
    return {key: metrics[key] for key in keys if key in metrics}


def numeric_anchors(release: dict) -> dict:
    def source(key):
        return read_json(ROOT / SOURCES[key])

    wg = source("wildguard-analysis")
    qwen = source("qwen-analysis")
    transfer = source("transfer-analysis")
    hate = source("hatexplain-analysis")
    result = {
        "evidence_revision": release["evidence_revision"],
        "metric_units": "Accuracy, recall and F1 are fractions, not percentages. Confusion rows are gold labels, columns predictions.",
        "interpretation": "Historical configurations only; later extensions reused previously examined tests. See studies.md for caveats.",
        "wildguard": {
            "source_id": "wildguard-analysis",
            "entries": [{"run": e["run"], "adapter": e["adapter"], "policy_id": e["policy_id"],
                         "roles": e["roles"], "metrics": compact_metrics(e["metrics"])} for e in wg["entries"]],
            "calibration_controls": [{"run": e["run"], "threshold": e["threshold"],
                                      "metrics": compact_metrics(e["metrics"])} for e in wg["calibration_controls"]],
        },
        "qwen": {
            "source_id": "qwen-analysis",
            "selected_test": [{"run": e["run"], "model": e["model"], "policy_id": e["policy_id"],
                               "metrics": compact_metrics(e["metrics"])} for e in qwen["entries"]
                              if e["split"] == "test" and "selected" in e["roles"]],
        },
        "transfer": {
            "source_id": "transfer-analysis", "source_selected": transfer["source_selected"],
            "pool_selected": transfer["pool_selected"],
            "test_matrix": {model: {policy: compact_metrics(m) for policy, m in policies.items()}
                            for model, policies in transfer["matrix"]["test"].items()},
        },
        "hatexplain": {
            "source_id": "hatexplain-analysis", "selections": hate["selections"],
            "test_conditions": [{"model": e["model"], "policy_id": e["policy_id"],
                                 "variant": e["variant"], "metrics": compact_metrics(e)}
                                for e in hate["conditions"] if not e["repeat"]],
        },
        "log_odds_ensembles": {},
    }
    for key in ("logits-wildguard", "logits-hate-specialists", "logits-hate-mixed"):
        data = source(key)
        result["log_odds_ensembles"][data["cohort"]] = {
            "source_id": key, "n": data["n"], "selection": data["selection"],
            "display_candidates": {name: {"threshold": data["all_candidates"][name].get("threshold"),
                                          "metrics": compact_metrics(data["all_candidates"][name]["metrics"])}
                                   for name in data["display_candidates"]},
            "highest_observed_test_single": data["highest_observed_test_single"],
        }
    return result


def installer_api():
    # run_path avoids an import-created __pycache__ inside the distributable package.
    return runpy.run_path(str(SKILL / "scripts" / "install.py"))


def manifest(release: dict) -> dict:
    return {"name": release["name"], "version": release["version"],
            "files": installer_api()["package_files"](SKILL)}


def check() -> dict:
    release = installer_api()["verify_package"](SKILL)
    version = release["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or release["release_tag"] != f"skill-v{version}":
        raise ValueError("Version and release tag must agree")
    frontmatter = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
    if f'name: {release["name"]}' not in frontmatter or f'version: "{version}"' not in frontmatter:
        raise ValueError("SKILL.md metadata and release.json disagree")
    if read_json(SKILL / "references" / "sources.json") != registry(release):
        raise ValueError("Source registry is stale; review and refresh it")
    if read_json(SKILL / "references" / "results.json") != numeric_anchors(release):
        raise ValueError("Numeric anchors differ from frozen evidence")
    for path in SKILL.rglob("*.md"):
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.is_relative_to(SKILL.resolve()) or not target.exists():
                raise ValueError(f"Broken or non-portable package link in {path.name}: {link}")
    return release


def build(output: Path) -> Path:
    release = check()
    output.mkdir(parents=True, exist_ok=True)
    path = output / f'safeguard-eval-skill-v{release["version"]}.zip'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(SKILL.rglob("*")):
            if item.is_file():
                info = zipfile.ZipInfo(f"safeguard-eval/{item.relative_to(SKILL).as_posix()}", (2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, item.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    (output / "SHA256SUMS").write_text(f"{digest(path.read_bytes())}  {path.name}\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["refresh", "check", "build"])
    parser.add_argument("--evidence-ref", help="Committed evidence revision for refresh; prose must be reviewed separately")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        if args.command == "refresh":
            release = read_json(SKILL / "release.json")
            if args.evidence_ref:
                release["evidence_revision"] = git("rev-parse", "--verify", f"{args.evidence_ref}^{{commit}}").decode().strip()
            sources = registry(release)
            anchors = numeric_anchors(release)
            write_json(SKILL / "release.json", release)
            write_json(SKILL / "references" / "sources.json", sources)
            write_json(SKILL / "references" / "results.json", anchors)
            write_json(SKILL / "manifest.json", manifest(release))
            print("Refreshed source hashes, numeric anchors, and package manifest. Review the prose before release.")
        elif args.command == "build":
            print(build(args.output))
        else:
            release = check()
            print(f'Checked Safeguard Eval {release["version"]}: {len(SOURCES)} pinned sources, numeric anchors, package hashes, and local links.')
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"Skill release check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
