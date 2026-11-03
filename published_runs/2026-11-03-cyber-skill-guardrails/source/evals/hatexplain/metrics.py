"""Binary decision quality with the original three-way labels retained in slices."""
from collections import Counter


def metric(rows):
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty or duplicate metric population')
    if any(r['prediction'] not in ('ALLOW', 'BLOCK', 'ERROR') for r in rows):
        raise ValueError('Unknown prediction')
    cm = {g: Counter({p: 0 for p in ('ALLOW', 'BLOCK', 'ERROR')}) for g in ('ALLOW', 'BLOCK')}
    for r in rows:
        cm[r['expected']][r['prediction']] += 1
    # Non-answers count as the wrong binary class for the primary F1 metric.
    tp = cm['BLOCK']['BLOCK']; tn = cm['ALLOW']['ALLOW']
    fp = cm['ALLOW']['BLOCK'] + cm['ALLOW']['ERROR']
    fn = cm['BLOCK']['ALLOW'] + cm['BLOCK']['ERROR']
    div = lambda a, b: a / b if b else None
    f1b = div(2 * tp, 2 * tp + fp + fn) or 0.
    f1a = div(2 * tn, 2 * tn + fp + fn) or 0.
    return dict(n=len(rows), accuracy=(tp + tn) / len(rows), macro_f1=(f1b + f1a) / 2,
                hate_f1=f1b, hate_recall=div(tp, tp + fn), errors=sum(v['ERROR'] for v in cm.values()),
                blocked=sum(r['prediction'] == 'BLOCK' for r in rows),
                false_blocks=cm['ALLOW']['BLOCK'], missed_hate=fn, confusion={k: dict(v) for k, v in cm.items()})


def report(rows):
    result = metric(rows)
    result['slices'] = {}
    for field in ('source_label', 'agreement', 'platform'):
        result['slices'][field] = {}
        for value in sorted({r[field] for r in rows}, key=str):
            part = [r for r in rows if r[field] == value]
            result['slices'][field][str(value)] = dict(metric(part), block_rate=sum(r['prediction'] == 'BLOCK' for r in part) / len(part))
    result['targets'] = {}
    for target in sorted({t for r in rows for t in r['targets']} - {'None'}):
        part = [r for r in rows if target in r['targets']]
        if len(part) >= 30:
            result['targets'][target] = metric(part)
    return result


def paired(a, b, reps=2000, seed=20261026):
    """Cluster-paired bootstrap; source-minus-reference; unadjusted intervals."""
    import numpy as np
    aa, bb = {r['id']: r for r in a}, {r['id']: r for r in b}
    if len(aa) != len(a) or len(bb) != len(b) or aa.keys() != bb.keys():
        raise ValueError('Unpaired populations')
    groups = sorted({r['group'] for r in a}); indexes = {g: i for i, g in enumerate(groups)}
    counts = np.zeros((len(groups), 2, 4), dtype=np.int64)
    fixed = broken = changed = 0
    for identifier in sorted(aa):
        x, y = aa[identifier], bb[identifier]
        if any(x[k] != y[k] for k in ('group', 'expected', 'source_label')):
            raise ValueError('Gold/group mismatch')
        correct_x, correct_y = x['prediction'] == x['expected'], y['prediction'] == y['expected']
        fixed += correct_x and not correct_y; broken += correct_y and not correct_x
        changed += x['prediction'] != y['prediction']
        for j, r in enumerate((x, y)):
            # TP, TN, FP, FN, including conservative failure assignment.
            idx = (0 if r['prediction'] == 'BLOCK' else 3) if r['expected'] == 'BLOCK' else (1 if r['prediction'] == 'ALLOW' else 2)
            counts[indexes[r['group']], j, idx] += 1
    rng = np.random.default_rng(seed)
    values = []
    for start in range(0, reps, 100):
        draws = rng.integers(0, len(groups), size=(min(100, reps - start), len(groups)))
        summed = counts[draws].sum(axis=1)
        tp, tn, fp, fn = [summed[:, :, i] for i in range(4)]
        accuracy = (tp + tn) / summed.sum(axis=2)
        f1b = np.divide(2*tp, 2*tp+fp+fn, out=np.zeros_like(tp, dtype=float), where=(2*tp+fp+fn)!=0)
        f1a = np.divide(2*tn, 2*tn+fp+fn, out=np.zeros_like(tn, dtype=float), where=(2*tn+fp+fn)!=0)
        f1 = (f1b + f1a) / 2
        values.extend(zip(accuracy[:, 0]-accuracy[:, 1], f1[:, 0]-f1[:, 1]))
    values = np.array(values)
    ma, mb = metric(a), metric(b)
    return dict(accuracy_delta=ma['accuracy']-mb['accuracy'], macro_f1_delta=ma['macro_f1']-mb['macro_f1'],
                accuracy_ci95=np.quantile(values[:, 0], [.025, .975]).tolist(),
                macro_f1_ci95=np.quantile(values[:, 1], [.025, .975]).tolist(),
                cases_fixed=int(fixed), cases_broken=int(broken), decisions_changed=int(changed),
                groups=len(groups), bootstrap_reps=reps, seed=seed,
                limitation='Unadjusted descriptive intervals; exclude policy-search and inference variance.')
