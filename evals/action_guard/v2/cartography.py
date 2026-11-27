"""Dataset cartography over the training log (Swayamdipta et al. 2020; design P9).

confidence = mean p(gold) across epochs; variability = its standard deviation.
Hard-to-learn items (low confidence, low variability) are listed for label review.

python -m evals.action_guard.v2.cartography DATA RUN_DIR
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main(data, run):
    rows = {json.loads(l)["id"]: json.loads(l) for l in Path(data).read_text().splitlines()}
    by = defaultdict(list)
    for l in (Path(run) / "cartography.jsonl").read_text().splitlines():
        r = json.loads(l)
        by[r["id"]].append(r["p_gold"])
    stats = []
    for i, ps in by.items():
        conf, var = statistics.fmean(ps), statistics.pstdev(ps)
        region = "easy" if conf >= 0.7 else "hard" if conf < 0.3 and var < 0.2 else "ambiguous"
        stats.append({"id": i, "confidence": round(conf, 3), "variability": round(var, 3), "region": region,
                      "decision": rows[i]["label"]["decision"], "variant": rows[i]["variant"], "principle": rows[i]["principle"],
                      "question": rows[i]["label"]["question"], "missing": rows[i]["label"]["missing"]})
    print("regions:", dict(Counter(s["region"] for s in stats)))
    for reg in ("hard", "ambiguous"):
        print(f"\n{reg} by decision:", dict(Counter(s["decision"] for s in stats if s["region"] == reg)))
    print("\nhard-to-learn items:")
    for s in sorted(stats, key=lambda s: s["confidence"]):
        if s["region"] == "hard":
            print(" ", json.dumps(s))
    (Path(run) / "cartography-summary.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
