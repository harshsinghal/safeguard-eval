"""Selection integrity checks; synthetic data only, no model inference."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.special import expit

from evals.smart_ensemble.common import align_scores, digest, write
from evals.smart_ensemble.infer import empty_result, attempt_id
from evals.jev.api import Ledger, RESERVE
from evals.smart_ensemble.learn import Search, describe, logistic, logodds, predict
from evals.smart_ensemble.study import check_freeze


class SmartEnsembleTests(unittest.TestCase):
    def test_alignment_rejects_missing_duplicate_and_changed_content(self):
        meta = [dict(id='a', expected='ALLOW', group='g', prompt_sha256='h')]
        row = dict(id='a', score=.2, prediction='ALLOW', prompt_sha256='h')
        self.assertEqual(align_scores(meta, [row])[0]['score'], .2)
        for bad in [[], [row, row], [{**row, 'prompt_sha256': 'other'}]]:
            with self.assertRaises(ValueError):
                align_scores(meta, bad)

    def test_unrelated_missing_component_does_not_invalidate_single(self):
        x = np.array([[.1, .5], [.9, .8]])
        valid = np.array([[True, False], [True, True]])
        native = np.array([[0, -1], [1, 1]])
        single = predict(dict(kind='raw', columns=[0]), x, valid, native)
        pair = predict(dict(kind='mean-probability', columns=[0, 1]), x, valid, native)
        self.assertEqual(single['prediction'], [0, 1])
        self.assertEqual(pair['prediction'], [-1, 1])
        self.assertIsNone(pair['score'][0])

    def test_exported_equation_reconstructs_classifier(self):
        rng = np.random.default_rng(12)
        x = rng.uniform(.01, .99, (80, 2))
        y = (x[:, 0] + .3*x[:, 1] > .65).astype(int)
        model = logistic(.1).fit(logodds(x), y)
        desc = describe(dict(kind='logistic', model=model, names=['a', 'b'], columns=[0, 1]))
        coefficients = np.array([desc['logodds_coefficients'][k] for k in ['a', 'b']])
        reconstructed = expit(desc['logodds_intercept'] + logodds(x) @ coefficients)
        np.testing.assert_allclose(reconstructed, model.predict_proba(logodds(x))[:, 1], atol=1e-12)

    def test_duplicate_groups_stay_together_in_oof(self):
        groups = np.repeat(np.arange(40), 2)
        y = np.repeat(np.arange(40) % 2, 2)
        x = (.2 + .6*y)[:, None]
        search = Search(['one'], x, y, np.ones_like(x, dtype=bool), groups)
        for group in set(groups):
            self.assertEqual(len(set(search.fold_ids[groups == group])), 1)
        result = search.subset(['one'])
        self.assertEqual(len(result['oof']['score']), len(y))

    def test_empty_input_stays_unresolved(self):
        result = empty_result(dict(id='empty', prompt_sha256='h'), 'jev')
        self.assertIsNone(result['score'])
        self.assertEqual(result['prediction'], 'ERROR')

    def test_retries_preserve_charges_and_require_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp)/'billing.sqlite', 0., cap=.02)
            for index in range(3):
                aid = attempt_id(ledger, 'request')
                self.assertEqual(aid, 'request' if index == 0 else f'request-retry-{index}')
                ledger.reserve(aid)
                with self.assertRaises(RuntimeError):
                    attempt_id(ledger, 'request')
                ledger.settle(aid, RESERVE, 'transport_upper_bound')
            with self.assertRaises(RuntimeError):
                attempt_id(ledger, 'request')
            self.assertAlmostEqual(ledger.totals()['total_accounted_usd'], 3*RESERVE)

    def test_freeze_detects_changed_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state/'policy.json').write_text('{}')
            write(state/'freeze.json', dict(artifacts={'policy.json': digest(state/'policy.json')}, sources={}))
            check_freeze(state)
            (state/'policy.json').write_text('{"changed":true}')
            with self.assertRaises(ValueError):
                check_freeze(state)


if __name__ == '__main__':
    unittest.main()
