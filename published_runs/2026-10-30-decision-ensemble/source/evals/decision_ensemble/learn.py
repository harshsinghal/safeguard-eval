"""Training-only fits; validation-only selections; no inference or test inputs."""
from collections import defaultdict

import numpy as np
from scipy.special import expit
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evals.ensemble.learn import weighted_fit
from evals.leaderboard.metrics import PROFILES, rank_key, select

SEED = 20261030
EPSILON = 1e-6
C_GRID = (.01, .1, 1., 10., 100.)
SCORE_FAMILIES = ("probability-logistic", "logodds-logistic", "equal-probability",
                  "equal-calibrated", "equal-logodds", "weighted", "forest")


def log_odds(x):
    x = np.asarray(x, dtype=np.float64)
    if not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
        raise ValueError("Probabilities must be finite and in [0, 1]")
    x = np.clip(x, EPSILON, 1 - EPSILON)
    return np.log(x) - np.log1p(-x)


def logistic(c):
    return make_pipeline(StandardScaler(), LogisticRegression(
        C=c, max_iter=2000, random_state=SEED))


def calibrators(x, y, groups):
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    out = np.zeros_like(x)
    seen = np.zeros(len(y), dtype=int)
    for train, held in splitter.split(x, y, groups):
        if set(groups[train]) & set(groups[held]):
            raise ValueError("Calibration fold has shared groups")
        for j in range(x.shape[1]):
            model = logistic(1.).fit(x[train, j:j + 1], y[train])
            out[held, j] = model.predict_proba(x[held, j:j + 1])[:, 1]
        seen[held] += 1
    if not np.all(seen == 1):
        raise ValueError("Calibration folds did not cover each fitting row once")
    full = [logistic(1.).fit(x[:, j:j + 1], y) for j in range(x.shape[1])]
    return out, full


def fit_candidates(names, x, y, valid, native, groups):
    """This interface accepts fitting data only, never validation or test labels."""
    complete = valid.all(axis=1)
    if len(np.unique(y[complete])) != 2:
        raise ValueError("Both fitting classes are required")
    xt, yt = x[complete], y[complete]
    z = log_odds(x)
    candidates = []
    for j, name in enumerate(names):
        own = valid[:, j]
        candidates.append(dict(id=f"single/{name}/raw", family="single", kind="raw", column=j))
        for representation in ("probability", "logodds"):
            features = x if representation == "probability" else z
            for c in C_GRID:
                candidates.append(dict(id=f"single/{name}/{representation}/C{c:g}",
                    family="single", kind=representation, column=j, C=c,
                    model=logistic(c).fit(features[own, j:j + 1], y[own])))
    oof, full = calibrators(xt, yt, np.asarray(groups)[complete])
    for family in ("equal-probability", "equal-calibrated", "equal-logodds"):
        candidates.append(dict(id=family, family=family, kind=family, calibrators=full))
    for strength in (0., .01, .1):
        weights, info = weighted_fit(oof, yt, strength)
        candidates.append(dict(id=f"weighted/lambda{strength:g}", family="weighted",
            kind="weighted", weights=weights, strength=strength, calibrators=full, optimization=info))
    for family, features in (("probability-logistic", xt),
                              ("logodds-logistic", z[complete]),
                              ("decision-logistic", native[complete].astype(float))):
        for c in C_GRID:
            candidates.append(dict(id=f"{family}/C{c:g}", family=family, kind=family,
                                   C=c, model=logistic(c).fit(features, yt)))
    for depth in (2, 4):
        for leaf in (20, 80):
            model = RandomForestClassifier(n_estimators=300, max_depth=depth,
                min_samples_leaf=leaf, random_state=SEED, n_jobs=2).fit(xt, yt)
            candidates.append(dict(id=f"forest/depth{depth}-leaf{leaf}", family="forest",
                                   kind="forest", depth=depth, leaf=leaf, model=model))
    candidates.append(dict(id="majority", family="majority", kind="majority"))
    return candidates, dict(fitting_rows=int(complete.sum()),
        excluded_fitting_rows=int((~complete).sum()),
        feature_names=names, calibration_folds=5,
        clipped_logodds_counts={name: int((valid[:, j] & ((x[:, j] < EPSILON) |
            (x[:, j] > 1 - EPSILON))).sum()) for j, name in enumerate(names)})


def values(candidate, x, valid, native):
    kind = candidate["kind"]
    j = candidate.get("column")
    good = valid[:, j] if j is not None else valid.all(axis=1)
    if kind == "raw":
        scores = x[:, j]
        predicted = native[:, j]
    elif kind in ("probability", "logodds"):
        features = x[:, j:j + 1]
        if kind == "logodds":
            features = log_odds(features)
        scores = candidate["model"].predict_proba(features)[:, 1]
        predicted = (scores >= .5).astype(int)
    elif kind == "equal-probability":
        scores = x.mean(axis=1)
        predicted = (scores >= .5).astype(int)
    elif kind == "equal-logodds":
        scores = expit(log_odds(x).mean(axis=1))
        predicted = (scores >= .5).astype(int)
    elif kind in ("weighted", "equal-calibrated"):
        calibrated = np.column_stack([m.predict_proba(x[:, k:k + 1])[:, 1]
            for k, m in enumerate(candidate["calibrators"])])
        scores = calibrated @ candidate["weights"] if kind == "weighted" else calibrated.mean(axis=1)
        predicted = (scores >= .5).astype(int)
    elif kind in ("probability-logistic", "logodds-logistic", "decision-logistic", "forest"):
        features = log_odds(x) if kind == "logodds-logistic" else native.astype(float) if kind == "decision-logistic" else x
        scores = candidate["model"].predict_proba(features)[:, 1]
        predicted = (scores >= .5).astype(int)
    elif kind == "majority":
        # The two-model cohort's exact tie is BLOCK, fixed before evaluation.
        predicted = (native.mean(axis=1) >= .5).astype(int)
        return dict(prediction=np.where(good, predicted, -1).tolist(), score=None)
    else:
        raise ValueError("Unknown candidate kind: " + kind)
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("Combiner produced invalid probabilities")
    return dict(prediction=np.where(good, predicted, -1).tolist(),
                score=[float(s) if ok else None for s, ok in zip(scores, good)])


def choose(names, candidates, y, x, valid, native):
    """Choose on validation only. All returned choices are frozen before test."""
    outputs = {c["id"]: values(c, x, valid, native) for c in candidates}
    buckets = defaultdict(list)
    for c in candidates:
        buckets[c["family"]].append(c["id"])
        if c["family"] == "single":
            buckets["single-" + names[c["column"]]].append(c["id"])
    selections, grids = {}, {}
    for group, ids in sorted(buckets.items()):
        selections[group], grids[group] = select(y, {i: outputs[i] for i in ids})
    selections["best-score-ensemble"] = {}
    for profile in PROFILES:
        eligible = [selections[f][profile] for f in SCORE_FAMILIES if selections[f][profile] is not None]
        selections["best-score-ensemble"][profile] = min(eligible, key=lambda r: rank_key(r, profile)) if eligible else None
    return selections, outputs, grids


def describe(candidates):
    def linear(model):
        scaler, lr = model.steps[0][1], model.steps[-1][1]
        coefficients = lr.coef_[0] / scaler.scale_
        return dict(feature_means=scaler.mean_.tolist(), feature_scales=scaler.scale_.tolist(),
            standardized_coefficients=lr.coef_[0].tolist(), standardized_intercept=float(lr.intercept_[0]),
            coefficients=coefficients.tolist(), intercept=float(lr.intercept_[0] - coefficients @ scaler.mean_))
    result = {}
    for c in candidates:
        row = {k: c[k] for k in ("id", "family", "kind", "column", "C", "depth", "leaf", "strength", "optimization") if k in c}
        if "weights" in c:
            row["weights"] = c["weights"].tolist()
        if "model" in c and c["kind"] != "forest":
            row["linear_parameters"] = linear(c["model"])
        if c["kind"] in ("weighted", "equal-calibrated"):
            row["calibrators"] = [linear(m) for m in c["calibrators"]]
        if c["kind"] == "forest":
            row["feature_importances"] = c["model"].feature_importances_.tolist()
        result[c["id"]] = row
    return result
