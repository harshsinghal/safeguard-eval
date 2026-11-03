"""Metrics and development-only operating-point selection.

Prediction codes: ALLOW=0, BLOCK=1, unresolved=-1. Unresolved decisions never
become artificial correct answers or disappear from class-recall denominators.
"""
import math

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

PROFILES = ("balanced", "false_block_limit", "catch_target")
THRESHOLDS = [i / 100 for i in range(101)] + [1.000000001]
SEED = 20261029


def divide(a, b):
    return float(a / b) if b else None


def counts(y, p):
    y, p = np.asarray(y), np.asarray(p)
    if y.shape != p.shape or not np.isin(y, [0, 1]).all() or not np.isin(p, [-1, 0, 1]).all():
        raise ValueError("Invalid or misaligned labels")
    return dict(tp=int(((y == 1) & (p == 1)).sum()),
                tn=int(((y == 0) & (p == 0)).sum()),
                fp=int(((y == 0) & (p == 1)).sum()),
                fn=int(((y == 1) & (p == 0)).sum()),
                error_allow=int(((y == 0) & (p == -1)).sum()),
                error_block=int(((y == 1) & (p == -1)).sum()))


def from_counts(c):
    tp, tn, fp, fn, ea, eb = [c[k] for k in ("tp", "tn", "fp", "fn", "error_allow", "error_block")]
    pos, neg = tp + fn + eb, tn + fp + ea
    n = pos + neg
    recall, specificity = divide(tp, pos), divide(tn, neg)
    f1b = divide(2 * tp, 2 * tp + fp + fn + eb)
    f1a = divide(2 * tn, 2 * tn + fp + fn + ea)
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    # MCC is a binary statistic here; do not silently omit unresolved outputs.
    mcc = None if ea + eb else ((tp * tn - fp * fn) / den if den else 0.0)
    return dict(n=n, positives=pos, negatives=neg, confusion=c,
                balanced_accuracy=(recall + specificity) / 2 if pos and neg else None,
                accuracy=divide(tp + tn, n), recall=recall, specificity=specificity,
                false_positive_rate=divide(fp, neg), false_negative_rate=divide(fn, pos),
                compliant_error_rate=divide(fp + ea, neg), violation_error_rate=divide(fn + eb, pos),
                precision=divide(tp, tp + fp), macro_f1=((f1a or 0) + (f1b or 0)) / 2,
                block_f1=f1b or 0.0, allow_f1=f1a or 0.0, mcc=mcc,
                false_blocks=fp, missed_violations=fn, unresolved=ea + eb,
                coverage=divide(n - ea - eb, n))


def metrics(y, p, scores=None):
    m = from_counts(counts(y, p))
    if scores is not None:
        s = np.array([float(v) if v is not None else np.nan for v in scores])
        valid = np.isfinite(s) & (np.asarray(p) != -1)
        yy = np.asarray(y)[valid]
        m["score_coverage"] = float(valid.mean())
        m["score_n"] = int(valid.sum())
        m["auroc"] = float(roc_auc_score(yy, s[valid])) if len(set(yy)) == 2 else None
        m["average_precision"] = float(average_precision_score(yy, s[valid])) if len(set(yy)) == 2 else None
    return m


def decisions(candidate, threshold):
    native = np.asarray(candidate["prediction"], dtype=int)
    if threshold is None:
        return native
    scores = candidate.get("score")
    if scores is None:
        raise ValueError("A categorical classifier cannot be thresholded")
    s = np.array([float(v) if v is not None else np.nan for v in scores])
    valid = np.isfinite(s) & (native != -1)
    return np.where(valid, (s >= threshold).astype(int), -1)


def rank_key(record, profile):
    m, t = record["metrics"], record["threshold"]
    tail = (-min(m["recall"], m["specificity"]), -m["macro_f1"],
            0 if t is None else 1, 0 if t is None else abs(t - .5),
            -1 if t is None else t, record["candidate"])
    if profile == "balanced":
        return (-m["balanced_accuracy"],) + tail
    if profile == "false_block_limit":
        return (-m["recall"], m["compliant_error_rate"]) + tail
    if profile == "catch_target":
        return (m["compliant_error_rate"], -m["recall"]) + tail
    raise ValueError(profile)


def eligible(m, profile):
    if m["balanced_accuracy"] is None:
        return False
    if profile == "false_block_limit":
        return m["compliant_error_rate"] <= .05 + 1e-12
    if profile == "catch_target":
        return m["recall"] >= .90 - 1e-12
    return True


def select(y, candidates):
    """Only development labels/outputs enter this function. No test arguments."""
    best = {p: None for p in PROFILES}
    grid = []
    for cid, candidate in sorted(candidates.items()):
        thresholds = [None] + (THRESHOLDS if candidate.get("score") is not None else [])
        for t in thresholds:
            m = metrics(y, decisions(candidate, t))
            row = dict(candidate=cid, threshold=t, metrics=m)
            grid.append(dict(candidate=cid, threshold=t, balanced_accuracy=m["balanced_accuracy"],
                             recall=m["recall"], compliant_error_rate=m["compliant_error_rate"],
                             macro_f1=m["macro_f1"], unresolved=m["unresolved"]))
            for profile in PROFILES:
                if eligible(m, profile) and (best[profile] is None or rank_key(row, profile) < rank_key(best[profile], profile)):
                    best[profile] = row
    return best, grid


def bootstrap(metadata, predictions, repetitions=2000):
    """Identical duplicate-group draws for all configurations enable pairing."""
    groups = sorted({r["group"] for r in metadata})
    gi = {g: i for i, g in enumerate(groups)}
    y = np.asarray([r["expected"] == "BLOCK" for r in metadata], dtype=int)
    names = sorted(predictions)
    cube = np.zeros((len(groups), len(names), 6), dtype=np.int16)
    for j, name in enumerate(names):
        for i, p in enumerate(predictions[name]):
            code = (0 if p == 1 else 3 if p == 0 else 5) if y[i] else (1 if p == 0 else 2 if p == 1 else 4)
            cube[gi[metadata[i]["group"]], j, code] += 1
    result = {name: {m: [] for m in ("balanced_accuracy", "recall", "specificity", "macro_f1", "mcc")} for name in names}
    rng = np.random.default_rng(SEED)
    for start in range(0, repetitions, 32):
        draw = rng.integers(0, len(groups), size=(min(32, repetitions - start), len(groups)))
        c = cube[draw].sum(axis=1)
        tp, tn, fp, fn, ea, eb = [c[:, :, i].astype(float) for i in range(6)]
        recall, specificity = tp / (tp + fn + eb), tn / (tn + fp + ea)
        f1b = np.divide(2 * tp, 2 * tp + fp + fn + eb, out=np.zeros_like(tp), where=(2 * tp + fp + fn + eb) > 0)
        f1a = np.divide(2 * tn, 2 * tn + fp + fn + ea, out=np.zeros_like(tn), where=(2 * tn + fp + fn + ea) > 0)
        den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        mcc = np.divide(tp * tn - fp * fn, den, out=np.zeros_like(tp), where=den > 0)
        mcc[ea + eb > 0] = np.nan
        arrays = dict(balanced_accuracy=(recall + specificity) / 2, recall=recall,
                      specificity=specificity, macro_f1=(f1a + f1b) / 2, mcc=mcc)
        for j, name in enumerate(names):
            for metric, arr in arrays.items():
                result[name][metric].extend(arr[:, j].tolist())
    return {name: {m: np.asarray(v) for m, v in values.items()} for name, values in result.items()}


def interval(draws):
    return np.quantile(draws, [.025, .975]).tolist() if np.isfinite(draws).all() else None
