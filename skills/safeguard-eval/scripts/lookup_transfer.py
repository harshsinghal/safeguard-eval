#!/usr/bin/env python3
"""Look up an exact historical policy-transfer comparison. Offline; no model calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
BASELINE = "wg-p0-taxonomy"
MODEL_NAMES = {
    "policylm": "PolicyLM 1.7B",
    "shieldstral": "Shieldstral 3B",
    "qwen-2b": "Qwen3.5 2B",
    "qwen-4b": "Qwen3.5 4B",
    "qwen-27b": "Qwen3.5 27B",
}


def lookup(source: str, recipient: str, package: Path = PACKAGE) -> dict:
    for role, name in (("source", source), ("recipient", recipient)):
        if name not in MODEL_NAMES:
            raise ValueError(f"Unknown {role} {name!r}. Choose exactly one of: {', '.join(MODEL_NAMES)}")
    anchors = json.loads((package / "references" / "results.json").read_text())
    registry = json.loads((package / "references" / "sources.json").read_text())
    if anchors["evidence_revision"] != registry["evidence_revision"]:
        raise ValueError("Result and source revisions differ; verify or reinstall the skill package.")
    transfer = anchors["transfer"]
    policy = transfer["source_selected"][source]
    cells = transfer["test_matrix"][recipient]
    initial, transferred = cells[BASELINE], cells[policy]
    if initial["n"] != transferred["n"]:
        raise ValueError("The comparison has different denominators; inspect the source before interpreting it.")
    citations = {s["id"]: s["url"] for s in registry["sources"]}

    def summary(metrics):
        confusion = metrics["confusion"]
        false_blocks = confusion["ALLOW"]["BLOCK"]
        missed = confusion["BLOCK"]["ALLOW"]
        failures = sum(row.get("ERROR", 0) for row in confusion.values())
        n = sum(sum(row.values()) for row in confusion.values())
        incorrect = false_blocks + missed + failures
        if (n != metrics["n"] or failures != metrics["errors"] or
                abs(metrics["accuracy"] - (n - incorrect) / n) > 1e-10):
            raise ValueError("Recorded metrics do not agree with confusion counts.")
        return {"accuracy_percent": round(metrics["accuracy"] * 100, 6),
                "false_blocks": false_blocks, "missed_harmful_prompts": missed,
                "output_failures": failures, "incorrect_total": incorrect}

    before, after = summary(initial), summary(transferred)
    return {
        "claim_kind": "recorded_result",
        "direction": f"Policy selected using {MODEL_NAMES[source]} -> classified using {MODEL_NAMES[recipient]}",
        "study": "2026-10-25 policy transfer; WildGuard prompt harmfulness",
        "evidence_revision": anchors["evidence_revision"],
        "policy_selected_using": {"id": source, "model": MODEL_NAMES[source]},
        "recipient_classifier": {"id": recipient, "model": MODEL_NAMES[recipient]},
        "selected_policy_id": policy,
        "source_selected_unchanged_initial_policy": policy == BASELINE,
        "selection_note": f"{MODEL_NAMES[source]}'s validation selected this policy for that source model. It was then evaluated on {MODEL_NAMES[recipient]}. Qwen3.5-27B wrote all revisions. This reports the source selection, not the recipient's separate choice from the shared policy pool.",
        "comparison": "Recipient's initial policy versus source-selected policy, within this study at the recipient's fixed native adapter and decision settings.",
        "test_n": initial["n"],
        "recipient_initial_policy": before,
        "recipient_with_source_selected_policy": after,
        "change_transferred_minus_initial": {
            "accuracy_percentage_points": round((transferred["accuracy"] - initial["accuracy"]) * 100, 6),
            **{k: after[k] - before[k] for k in
               ("false_blocks", "missed_harmful_prompts", "output_failures", "incorrect_total")},
        },
        "limits": "One bounded search on a previously examined test set; not a best-possible model ranking, causal architecture comparison, or validation of a user's new policy.",
        "sources": {"matrix": citations[transfer["source_id"]], "readout": citations["transfer-readout"]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=MODEL_NAMES, help="Model used to select the policy, not its writer")
    parser.add_argument("--recipient", choices=MODEL_NAMES, help="Model classifying content with that policy")
    parser.add_argument("--list", action="store_true", help="List recorded model IDs")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(MODEL_NAMES, indent=2))
        return
    if not args.source or not args.recipient:
        parser.error("Both --source and --recipient are required; use --list for recorded model IDs.")
    try:
        result = lookup(args.source, args.recipient)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Lookup unavailable: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
