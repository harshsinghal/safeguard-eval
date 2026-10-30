"""Guard the boundary between published evidence and an integrated comparison."""
import copy
import unittest

from evals.leaderboard.extend_decision_ensembles import (
    FAMILIES, mapped_choices, require_same_order, verify_results,
)


class LeaderboardExtensionTests(unittest.TestCase):
    def test_rejects_reordering_even_when_population_sets_match(self):
        rows = [dict(id=str(i), expected="ALLOW", group=str(i), prompt_sha256=str(i)) for i in range(2)]
        require_same_order(rows, rows)
        for bad in (rows[::-1], rows[:1], [rows[0], rows[0]],
                    [rows[0], dict(rows[1], expected="BLOCK")],
                    [rows[0], dict(rows[1], prompt_sha256="changed")]):
            with self.assertRaises(ValueError):
                require_same_order(rows, bad)

    def test_id_mapping_preserves_cutoffs_metrics_and_ineligible_profiles(self):
        choices = {"balanced": dict(candidate="c", threshold=.45, metrics={"accuracy": .8}),
                   "false_block_limit": None}
        mapped = mapped_choices(choices, "new/")
        self.assertEqual(mapped["balanced"]["candidate"], "new/c")
        self.assertEqual(choices["balanced"]["candidate"], "c")
        self.assertEqual(mapped["balanced"]["threshold"], .45)
        self.assertIsNone(mapped["false_block_limit"])
        self.assertEqual(len(FAMILIES), 9)
        self.assertFalse({"single", "best-score-ensemble"} & set(FAMILIES))

    def test_only_rank_can_change_for_a_previous_entry(self):
        row = dict(key="balanced/old", group="old", rank=1, metrics={"accuracy": .8}, threshold=.6)
        prior = {"datasets": {"wildguard": {"profiles": {"balanced": {"rows": [row], "gaps": []}}}}}
        current = copy.deepcopy(prior)
        target = current["datasets"]["wildguard"]["profiles"]["balanced"]["rows"][0]
        target["rank"] = 3
        verify_results(prior, {}, current)
        for key, value in (("threshold", .7), ("metrics", {"accuracy": .81})):
            bad = copy.deepcopy(current)
            bad["datasets"]["wildguard"]["profiles"]["balanced"]["rows"][0][key] = value
            with self.assertRaises(ValueError):
                verify_results(prior, {}, bad)


if __name__ == "__main__":
    unittest.main()
