"""Test-set report for frozen guards against the adjudicated test labels."""
import json
from pathlib import Path

from .evaluate import evaluate, load_preds
from .guards import ordinal_decision

ROOT = Path(__file__).resolve().parents[2]


def test_rows():
    return [json.loads(l) for l in (ROOT / "work/action-guard/data/test.jsonl").read_text().splitlines()]


def test_labels():
    return json.loads((ROOT / "docs/action-guard/test-labels.json").read_text())


def shieldstral_at(preds, cutoff):
    return {i: {"decision": ordinal_decision(r["level_probs"], cutoff) if r.get("level_probs") else None} for i, r in preds.items()}


def table(systems):
    rows, refs = test_rows(), test_labels()
    out = {}
    for name, preds in systems.items():
        out[name] = evaluate(rows, refs, preds, by=("split", "policy"))
    return out
