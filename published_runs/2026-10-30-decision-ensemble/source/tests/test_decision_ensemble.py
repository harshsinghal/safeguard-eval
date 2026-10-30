import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from evals.decision_ensemble import learn, study


class DecisionEnsembleTests(unittest.TestCase):
    def test_log_odds_handles_native_endpoints_and_rejects_invalid_scores(self):
        z = learn.log_odds(np.array([0., .5, 1.]))
        self.assertTrue(np.isfinite(z).all())
        self.assertAlmostEqual(z[0], np.log(1e-6 / (1 - 1e-6)))
        self.assertAlmostEqual(z[1], 0.)
        self.assertAlmostEqual(z[2], -z[0])
        for x in ([-.1], [1.1], [np.nan], [np.inf]):
            with self.assertRaises(ValueError): learn.log_odds(x)

    def test_missing_member_remains_unresolved_but_does_not_penalize_other_single(self):
        x = np.array([[.1, .9], [.7, .8]])
        valid = np.array([[True, False], [True, True]])
        native = np.array([[0, -1], [1, 1]])
        combined = learn.values(dict(kind="equal-probability"), x, valid, native)
        self.assertEqual(combined["prediction"], [-1, 1])
        self.assertIsNone(combined["score"][0])
        single = learn.values(dict(kind="raw", column=0), x, valid, native)
        self.assertEqual(single["prediction"], [0, 1])

    def test_majority_uses_native_labels_and_has_no_tunable_score(self):
        out = learn.values(dict(kind="majority"), np.array([[.1, .1]]),
                           np.array([[True, True]]), np.array([[0, 1]]))
        self.assertEqual(out, dict(prediction=[1], score=None))

    def test_native_single_does_not_reconstruct_tie_decision_from_probability(self):
        out = learn.values(dict(kind="raw", column=0), np.array([[.5]]),
                           np.array([[True]]), np.array([[0]]))
        self.assertEqual(out["prediction"], [0])

    def test_fitted_scaling_never_uses_held_out_distribution(self):
        train = np.array([[.1], [.2], [.8], [.9]])
        model = learn.logistic(1.).fit(train, [0, 0, 1, 1])
        before = model.steps[0][1].mean_.copy()
        learn.values(dict(kind="probability-logistic", model=model), np.full((10, 1), .99),
                     np.ones((10, 1), dtype=bool), np.ones((10, 1), dtype=int))
        np.testing.assert_array_equal(before, model.steps[0][1].mean_)
        self.assertAlmostEqual(before[0], .5)

    def test_saved_equation_matches_standardized_pipeline(self):
        x = np.array([[.1, .2], [.8, .6], [.9, .7], [.2, .1]])
        model = learn.logistic(1.).fit(x, [0, 1, 1, 0])
        c = dict(id="x", family="probability-logistic", kind="probability-logistic", model=model)
        p = learn.describe([c])["x"]["linear_parameters"]
        linear = x @ np.array(p["coefficients"]) + p["intercept"]
        np.testing.assert_allclose(1 / (1 + np.exp(-linear)), model.predict_proba(x)[:, 1])

    def test_out_of_fold_calibration_keeps_duplicate_groups_together(self):
        rng = np.random.default_rng(1)
        x = rng.uniform(.01, .99, (100, 2))
        y = np.repeat(np.tile([0, 1], 25), 2)
        groups = np.repeat(np.arange(50), 2)
        oof, full = learn.calibrators(x, y, groups)
        self.assertEqual(oof.shape, x.shape)
        self.assertTrue(np.isfinite(oof).all())
        self.assertEqual(len(full), 2)

    def test_reference_alignment_rejects_dropped_cases_and_changed_labels(self):
        meta = [dict(id="a", expected="ALLOW", group="g", prompt_sha256="h")]
        old = dict(metadata=list(meta), candidates={"c": dict(prediction=[0], score=[.1])})
        self.assertEqual(study.ref_values(meta, old, "c")["score"], [.1])
        with self.assertRaises(ValueError): study.ref_values(meta, {**old, "metadata": []}, "c")
        changed = [{**meta[0], "expected": "BLOCK"}]
        with self.assertRaises(ValueError): study.ref_values(changed, old, "c")

    def test_freeze_rejects_changed_development_or_fitted_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "selection.json"
            artifact.write_text('{}')
            study.write(root / "registration.json", dict(source_hashes={}))
            study.write(root / "freeze.json", dict(artifact_hashes={"selection.json": study.digest(artifact)}))
            study.check_freeze(root)
            artifact.write_text('{"threshold": 0.9}')
            with self.assertRaisesRegex(ValueError, "Changed registered"): study.check_freeze(root)

    def test_normalization_rejects_confidence_substituted_for_block_probability(self):
        row = dict(id="a", expected="ALLOW", prediction="ALLOW", score=.9,
                   probabilities={"ALLOW": .9, "BLOCK": .1}, split="fit")
        with mock.patch.dict(study.COUNTS, {"fit": 1}), mock.patch.dict(study.LABELS, {"fit": {"ALLOW": 1}}):
            with self.assertRaisesRegex(ValueError, "BLOCK probability"): study.normalize([row], "fit")


if __name__ == "__main__":
    unittest.main()
