import unittest

import numpy as np
from sklearn.metrics import balanced_accuracy_score, f1_score, matthews_corrcoef

from evals.leaderboard.archive import aligned, disjoint, normalize
from evals.leaderboard.metrics import bootstrap, decisions, eligible, interval, metrics, select


class LeaderboardMetricsTests(unittest.TestCase):
    def test_known_jev_tradeoff(self):
        y = [0] * 1330 + [1] * 594
        native = [0] * 940 + [1] * 390 + [0] * 88 + [1] * 506
        tuned = [0] * 1196 + [1] * 134 + [0] * 238 + [1] * 356
        a, b = metrics(y, native), metrics(y, tuned)
        self.assertAlmostEqual(a['balanced_accuracy'], .7793093845725425)
        self.assertGreater(a['balanced_accuracy'], b['balanced_accuracy'])
        self.assertLess(a['accuracy'], b['accuracy'])
        self.assertLess(a['macro_f1'], b['macro_f1'])
        for p, m in [(native, a), (tuned, b)]:
            self.assertAlmostEqual(m['balanced_accuracy'], balanced_accuracy_score(y, p))
            self.assertAlmostEqual(m['macro_f1'], f1_score(y, p, average='macro'))
            self.assertAlmostEqual(m['mcc'], matthews_corrcoef(y, p))

    def test_majority_allow_is_not_a_strong_balanced_classifier(self):
        m = metrics([0] * 99 + [1], [0] * 100)
        self.assertEqual(m['accuracy'], .99)
        self.assertEqual(m['balanced_accuracy'], .5)
        self.assertEqual(m['mcc'], 0)

    def test_unresolved_outputs_stay_in_denominators(self):
        m = metrics([0, 0, 1, 1], [0, -1, 1, -1])
        self.assertEqual(m['accuracy'], .5)
        self.assertEqual(m['balanced_accuracy'], .5)
        self.assertEqual(m['unresolved'], 2)
        self.assertIsNone(m['mcc'])
        self.assertEqual(m['false_positive_rate'], 0)
        self.assertEqual(m['compliant_error_rate'], .5)
        self.assertFalse(eligible(m, 'false_block_limit'))

    def test_scores_never_repair_failed_responses(self):
        c = dict(prediction=[-1, 0, 1], score=[.99, .9, .1])
        self.assertEqual(decisions(c, .5).tolist(), [-1, 1, 0])
        self.assertEqual(decisions(c, None).tolist(), [-1, 0, 1])
        with self.assertRaises(ValueError):
            decisions(dict(prediction=[0], score=None), .5)

    def test_selection_only_sees_development_and_uses_profiles(self):
        y = [0] * 20 + [1] * 10
        c = dict(prediction=[0] * 15 + [1] * 5 + [0] * 2 + [1] * 8,
                 score=[.1] * 15 + [.6] * 5 + [.4] * 2 + [.9] * 8)
        chosen, _ = select(y, {'candidate': c})
        for profile, choice in chosen.items():
            self.assertTrue(eligible(choice['metrics'], profile))
        self.assertEqual(chosen['false_block_limit']['metrics']['recall'], .8)
        self.assertEqual(chosen['catch_target']['metrics']['recall'], 1)
        self.assertEqual(chosen['catch_target']['metrics']['false_positive_rate'], .25)
        # Test predictions are not an argument and cannot choose the cutoff.
        _, again = select(y, {'candidate': c})
        self.assertEqual(again, select(y, {'candidate': c})[1])

    def test_native_tie_and_infeasible_categorical_target(self):
        y = [0, 0, 1, 1]
        c = dict(prediction=[0, 0, 1, 0], score=[.1, .2, .8, .4])
        chosen, _ = select(y, {'b': c, 'a': c})
        self.assertEqual(chosen['balanced']['candidate'], 'a')
        native = dict(prediction=[0, 0, 1, 0], score=None)
        fixed, _ = select(y, {'fixed': native})
        self.assertIsNone(fixed['balanced']['threshold'])
        self.assertIsNone(fixed['catch_target'])
        perfect = dict(prediction=[0, 0, 1, 1], score=[.1, .2, .8, .9])
        self.assertIsNone(select(y, {'perfect': perfect})[0]['balanced']['threshold'])

    def test_population_alignment_rejects_changed_evidence(self):
        meta = [dict(id='a', expected='ALLOW', prompt_sha256='sha', group='g')]
        row = dict(meta[0], prediction='ALLOW', score=.2)
        for bad in [[], [row, row], [dict(row, expected='BLOCK')], [dict(row, prompt_sha256='other')], [dict(row, group='other')]]:
            with self.assertRaises(ValueError):
                aligned(meta, bad)
        no_group = {k: v for k, v in row.items() if k != 'group'}
        self.assertEqual(normalize(meta, [no_group])['prediction'], [0])

    def test_disjointness_checks_hashes_and_groups_not_only_ids(self):
        a = [dict(id='a', prompt_sha256='s1', group='g1')]
        for b in [dict(id='b', prompt_sha256='s1', group='g2'), dict(id='b', prompt_sha256='s2', group='g1')]:
            with self.assertRaises(ValueError):
                disjoint(a, [b])

    def test_single_class_slice_has_no_balanced_accuracy(self):
        self.assertIsNone(metrics([0, 0], [0, 1])['balanced_accuracy'])

    def test_score_metrics_do_not_invent_probabilities(self):
        m = metrics([0, 1], [0, 1])
        self.assertNotIn('auroc', m)
        m = metrics([0, 1, 0, 1], [0, 1, -1, 0], [.1, .9, .99, .3])
        self.assertEqual(m['score_coverage'], .75)
        self.assertEqual(m['auroc'], 1)

    def test_paired_bootstrap_respects_duplicate_groups(self):
        meta = [dict(id=str(i), group=str(i // 2), expected='BLOCK' if i % 2 else 'ALLOW') for i in range(20)]
        p = np.array([i % 2 for i in range(20)])
        b = bootstrap(meta, {'a': p, 'b': p}, repetitions=100)
        self.assertEqual(interval(b['a']['balanced_accuracy'] - b['b']['balanced_accuracy']), [0, 0])
        self.assertEqual(interval(b['a']['balanced_accuracy']), [1, 1])


if __name__ == '__main__':
    unittest.main()
