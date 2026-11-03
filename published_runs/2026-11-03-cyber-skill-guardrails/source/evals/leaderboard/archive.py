"""Read-only adapters for the project's existing, prompt-free evidence archives."""
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np

from evals.ensemble_logits.learn import predict as predict_fitted
from evals.ensemble.learn import validity

ARCHIVES = {"wildguard": "2026-10-24-wildguard", "qwen": "2026-10-25-qwen",
            "transfer": "2026-10-25-policy-transfer", "hatexplain": "2026-10-26-hatexplain",
            "ensemble": "2026-10-27-ensemble", "logits": "2026-10-28-ensemble-logits",
            "jev": "2026-10-29-jev", "frontier": "2026-10-25-frontier-pilot"}
MODELS = {
    "policylm": ("PolicyLM 1.7B", "Specialist", "musubilabs/policylm-1.7b"),
    "shieldstral": ("Shieldstral 3B", "Specialist", "mistralai/Shieldstral-1.0-3B"),
    "cope": ("CoPE", "Specialist", "zentropi-ai/cope-b-a4b"),
    "safeguard": ("GPT-OSS Safeguard 20B", "Specialist", "openai/gpt-oss-safeguard-20b"),
    "wildguard": ("WildGuard 7B", "Task-specific", "allenai/wildguard"),
    "qwen-2b": ("Qwen3.5 2B", "General-purpose", "Qwen/Qwen3.5-2B"),
    "qwen-4b": ("Qwen3.5 4B", "General-purpose", "Qwen/Qwen3.5-4B"),
    "qwen-9b": ("Qwen3.5 9B", "General-purpose", "Qwen/Qwen3.5-9B"),
    "qwen-27b": ("Qwen3.5 27B", "General-purpose", "Qwen/Qwen3.5-27B"),
    "qwen-35b-a3b": ("Qwen3.5 35B-A3B", "General-purpose", "Qwen/Qwen3.5-35B-A3B"),
    "jev": ("Jev 1.14", "Typed classifier", "typesafe/jev-1.14-20261014"),
}
FAMILIES = {"equal-raw": "Equal probability average", "equal-calibrated": "Calibrated probability average",
            "weighted": "Learned weighted average", "logistic": "Logistic regression · probabilities",
            "forest": "Random forest", "logit-logistic": "Logistic regression · log-odds",
            "logit-equal": "Equal log-odds average"}
COHORTS = {"wildguard-specialists": ("wildguard", ["policylm", "shieldstral", "cope"]),
           "hatexplain-specialists": ("hatexplain", ["policylm", "shieldstral"]),
           "hatexplain-mixed": ("hatexplain", ["policylm", "shieldstral", "qwen-4b"])}
META = ("id", "expected", "prompt_sha256", "group", "subcategory", "adversarial", "source_label", "platform", "agreement")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with (gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)) as f:
        return json.load(f)


def read_rows(path):
    with (gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)) as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=None if path.suffix == ".gz" else 2, sort_keys=True, allow_nan=False) + "\n").encode()
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(data, mtime=0))
    else:
        path.write_bytes(data)


def aligned(metadata, rows):
    by_id = {r["id"]: r for r in rows}
    if len(by_id) != len(rows) or set(by_id) != {r["id"] for r in metadata}:
        raise ValueError("Missing, extra, or duplicate predictions")
    for r in metadata:
        other = by_id[r["id"]]
        for k in ("expected", "prompt_sha256", "group"):
            # Jev's HateXplain export omitted groups. Canonical original groups
            # supply bootstrap membership only after exact ID/label/hash checks.
            if k == "group" and k not in other:
                continue
            if r[k] != other.get(k):
                raise ValueError(f"Population mismatch at {r['id']}: {k}")
    return [by_id[r["id"]] for r in metadata]


def normalize(metadata, rows):
    rows = aligned(metadata, rows)
    codes = {"ALLOW": 0, "BLOCK": 1, "ERROR": -1}
    if any(r.get("prediction") not in codes for r in rows):
        raise ValueError("Unknown prediction label")
    p = [codes[r["prediction"]] for r in rows]
    s = [r.get("score") for r in rows]
    if not any(v is not None for v in s):
        s = None
    elif any(v is not None and (not isinstance(v, (int, float)) or not np.isfinite(v) or not 0 <= v <= 1) for v in s):
        raise ValueError("Invalid probability score")
    return dict(prediction=p, score=s)


def disjoint(a, b):
    for key in ("id", "prompt_sha256", "group"):
        if {r[key] for r in a} & {r[key] for r in b}:
            raise ValueError(f"Fitting/validation/test overlap: {key}")


def slug(manifest):
    if manifest["adapter"] == "qwen":
        return "qwen-" + manifest["model"].split("Qwen3.5-")[-1].lower()
    return manifest["adapter"]


class Archive:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.base = self.root / "published_runs"
        self.inputs = {}
        self.specs = {}
        self.excluded = []
        self.replay = []
        self._models = {}
        self.metadata = {}
        self._predictions = {}
        self._replay_cache = {}
        for dataset in ("wildguard", "hatexplain"):
            self.metadata[dataset] = {}
            for split in ("validation", "test"):
                run = f"policylm-{split}-p0" if dataset == "wildguard" else f"policylm--p0--markdown--{split}"
                p = self.base / ARCHIVES[dataset] / "runs" / run / "predictions.jsonl.gz"
                rr = self.rows(p)
                self.metadata[dataset][split] = sorted([{k: r[k] for k in META if k in r} for r in rr], key=lambda r: r["id"])
            disjoint(self.metadata[dataset]["validation"], self.metadata[dataset]["test"])
        if len(self.metadata["wildguard"]["test"]) != 1699 or len(self.metadata["hatexplain"]["test"]) != 1924:
            raise ValueError("Unexpected canonical test populations")

    def track(self, path):
        path = Path(path).resolve()
        rel = str(path.relative_to(self.root))
        self.inputs[rel] = digest(path)
        return rel

    def json(self, path):
        self.track(path)
        return read(path)

    def rows(self, path):
        self.track(path)
        return read_rows(path)

    def discover_raw(self):
        for key in ("wildguard", "qwen", "transfer", "hatexplain"):
            folder = self.base / ARCHIVES[key]
            dataset = "hatexplain" if key == "hatexplain" else "wildguard"
            paired = defaultdict(lambda: defaultdict(list))
            for path in sorted(folder.rglob("manifest.json")):
                m = self.json(path)
                if m.get("split") not in ("validation", "test"):
                    continue
                pred = path.parent / "predictions.jsonl.gz"
                if not pred.exists():
                    continue
                if m.get("repeat") or "repeat" in path.parent.name:
                    self.excluded.append(dict(path=str(path.parent.relative_to(self.root)), reason="repeat diagnostic"))
                    continue
                ident = (slug(m), m.get("revision"), m.get("policy_sha256"), m.get("variant", "original"))
                paired[ident][m["split"]].append((path, m))
            for ident, splits in sorted(paired.items(), key=lambda item: str(item[0])):
                if set(splits) != {"validation", "test"}:
                    for split, records in splits.items():
                        for path, m in records:
                            self.excluded.append(dict(path=str(path.parent.relative_to(self.root)), reason=f"no matching {'test' if split == 'validation' else 'validation'} run", model=ident[0], dataset=dataset))
                    continue
                if any(len(v) != 1 for v in splits.values()):
                    raise ValueError(f"Ambiguous paired run: {key}, {ident}")
                vp, vm = splits["validation"][0]
                tp, tm = splits["test"][0]
                model = ident[0]
                cid = f"{dataset}/{key}/{vp.parent.name}"
                self.specs[cid] = dict(id=cid, dataset=dataset, group=model, model=model,
                    label=MODELS[model][0], category=MODELS[model][1], model_id=MODELS[model][2],
                    revision=ident[1], policy=vm["policy_id"], policy_sha256=ident[2], adapter=vm["adapter"],
                    variant=ident[3], kind="raw", source_archive=ARCHIVES[key],
                    validation=self.track(vp.parent / "predictions.jsonl.gz"),
                    test=self.track(tp.parent / "predictions.jsonl.gz"),
                    validation_manifest=self.track(vp), test_manifest=self.track(tp),
                    fitting_rows=None, validation_rows=len(self.metadata[dataset]["validation"]))
        for dataset in ("wildguard", "hatexplain"):
            folder = self.base / ARCHIVES["jev"]
            interface = self.json(folder / "policies" / dataset / "interface.json")
            for policy in ("brief", "detailed", "examples"):
                cid = f"{dataset}/jev/{policy}"
                self.specs[cid] = dict(id=cid, dataset=dataset, group="jev", model="jev", label=MODELS["jev"][0],
                    category=MODELS["jev"][1], model_id=MODELS["jev"][2], revision="20261014", policy=policy,
                    adapter="OpenRouter Decisions Choice", variant="native instructions + criteria", kind="raw",
                    source_archive=ARCHIVES["jev"], policy_interface=interface,
                    validation=self.track(folder / "predictions" / dataset / "validation" / (policy + ".jsonl.gz")),
                    test=self.track(folder / "predictions" / dataset / "test" / (policy + ".jsonl.gz")),
                    fitting_rows=1024, validation_rows=len(self.metadata[dataset]["validation"]))

    def models(self, path):
        path = Path(path)
        rel = self.track(path)
        if rel not in self._models:
            archive = path.parents[2]
            checksum = self.json(archive / "checksums.json")["sha256"]
            if checksum[str(path.relative_to(archive))] != digest(path):
                raise ValueError("Archived fitted-model hash mismatch")
            # Only deserialize our own checksum-verified project artifact.
            self._models[rel] = {c["id"]: c for c in joblib.load(path)}
        return self._models[rel]

    def discover_fitted(self):
        data = self.json(self.base / ARCHIVES["ensemble"] / "data-manifest.json")
        for key in ("ensemble", "logits"):
            folder = self.base / ARCHIVES[key]
            for cohort, (dataset, names) in COHORTS.items():
                mf = folder / "cohorts" / cohort / "models.joblib"
                f = self.json(mf.parent / "freeze.json")
                source = {}
                for name in names:
                    sha = data["policies"][dataset + "/" + name]["sha256"]
                    candidates = [s for s in self.specs.values() if s["dataset"] == dataset and s.get("model") == name
                                  and s.get("policy_sha256") == sha and s["source_archive"] == ARCHIVES["hatexplain" if dataset == "hatexplain" else "wildguard"]]
                    if len(candidates) != 1:
                        raise ValueError(f"Ambiguous ensemble input: {cohort}/{name}")
                    source[name] = candidates[0]["id"]
                    fitting = self.rows(folder / "scores" / dataset / name / "fit.jsonl.gz")
                    disjoint(fitting, self.metadata[dataset]["validation"])
                    disjoint(fitting, self.metadata[dataset]["test"])
                for cid, c in self.models(mf).items():
                    # Raw individual scores are already candidates with both native and tuned cutoffs.
                    if c["kind"] == "single-raw":
                        continue
                    single = c["family"] == "single"
                    model = names[c["column"]] if single else None
                    group = model if single else cohort + "/" + c["family"]
                    rid = f"{dataset}/{key}/{cohort}/{cid}"
                    self.specs[rid] = dict(id=rid, dataset=dataset, group=group, model=model,
                        label=MODELS[model][0] if single else FAMILIES[c["family"]] + (" · specialists + Qwen" if cohort.endswith("mixed") else " · specialists"),
                        category=MODELS[model][1] if single else "Ensemble",
                        model_id=MODELS[model][2] if single else "+".join(MODELS[n][2] for n in names),
                        kind="fitted", family=c["family"], fitted_kind=c["kind"], policy="; ".join(self.specs[source[n]]["policy"] for n in ([model] if single else names)),
                        source_archive=ARCHIVES[key], cohort=cohort, features=names, base_candidates=source,
                        model_file=self.track(mf), fitted_id=cid, original_threshold=c["threshold"],
                        archived_test=self.track(mf.parent / "test-predictions.jsonl.gz"),
                        fitting_rows=f["fit_n"], original_validation_rows=f["validation_n"],
                        validation_rows=len(self.metadata[dataset]["validation"]))

    def values(self, spec, split):
        cache = (spec["id"], split)
        if cache in self._predictions:
            return self._predictions[cache]
        dataset = spec["dataset"]
        meta = self.metadata[dataset][split]
        if spec["kind"] == "raw":
            value = normalize(meta, self.rows(self.root / spec[split]))
        else:
            base = [self.values(self.specs[spec["base_candidates"][n]], split) for n in spec["features"]]
            scores = np.array([[v if v is not None else .5 for v in b["score"]] for b in base]).T
            valid = np.array([[p != -1 and s is not None for p, s in zip(b["prediction"], b["score"])] for b in base]).T
            fitted = self.models(self.root / spec["model_file"])[spec["fitted_id"]]
            out = predict_fitted(fitted, scores)
            if not np.isfinite(out).all() or np.any(out < 0) or np.any(out > 1):
                raise ValueError("Invalid replayed fitted score")
            # The original helper only detects 'single-*'; the logit-single kind
            # is 'single-logit', so the same column-level failure logic applies.
            ok = validity(fitted, valid)
            prediction = np.where(ok, (out >= spec["original_threshold"]).astype(int), -1)
            value = dict(prediction=prediction.tolist(), score=out.tolist())
        self._predictions[cache] = value
        return value

    def verify_test_replay(self, spec, value):
        if spec["kind"] != "fitted":
            return
        path = spec["archived_test"]
        if path not in self._replay_cache:
            grouped = defaultdict(list)
            for r in self.rows(self.root / path):
                grouped[r["candidate"]].append(r)
            self._replay_cache[path] = {k: normalize(self.metadata[spec["dataset"]]["test"], v) for k, v in grouped.items()}
        old = self._replay_cache[path][spec["fitted_id"]]
        np.testing.assert_allclose(old["score"], value["score"], rtol=1e-10, atol=1e-12)
        if old["prediction"] != value["prediction"]:
            raise ValueError("Replayed fitted decisions differ from the archive")
        self.replay.append(dict(candidate=spec["id"], n=len(old["prediction"]), matched=True))

    def coverage(self):
        table = []
        for model, (label, category, ident) in MODELS.items():
            record = dict(model=label, model_id=ident, category=category)
            for dataset in ("wildguard", "hatexplain"):
                candidates = [s for s in self.specs.values() if s["dataset"] == dataset and s.get("model") == model]
                record[dataset] = "full test" if candidates else "not evaluated"
            table.append(record)
        registry = self.json(self.base / ARCHIVES["frontier"] / "source/evals/frontier_api/registry.json")
        for model, m in registry["models"].items():
            table.append(dict(model=m["id"], model_id=m["id"], category="Frontier API pilot",
                              wildguard="32 fitting examples only; unranked", hatexplain="not evaluated"))
        return table
