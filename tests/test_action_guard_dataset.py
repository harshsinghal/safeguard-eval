import json
import tempfile
import unittest
from pathlib import Path

from evals.action_guard import dataset, generator


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "data"
        dataset.build(cls.out)
        cls.rows = {s: [json.loads(l) for l in (cls.out / f"{s}.jsonl").read_text().splitlines()]
                    for s in ("train", "validation", "test_seen", "test_unseen_family", "test_unseen_dialect", "test")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_heldout_families_policy_and_dialect_never_reach_training(self):
        for split in ("train", "validation"):
            for r in self.rows[split]:
                self.assertNotIn(r["family"], generator.HELDOUT_FAMILIES)
                self.assertNotEqual(r["policy"], "heldout-prose")
                self.assertFalse(r["dialect"] == "query" and r["object"] in generator.HELDOUT_DIALECT_OBJECTS, r["id"])

    def test_no_scenario_crosses_splits(self):
        owner = {}
        for split, rows in self.rows.items():
            if split == "test":
                continue
            for r in rows:
                self.assertEqual(owner.setdefault(r["scenario_id"], split), split, r["scenario_id"])

    def test_no_identical_guard_input_crosses_train_and_test(self):
        train_inputs = {r["input"] for r in self.rows["train"]} | {r["input"] for r in self.rows["validation"]}
        self.assertFalse(train_inputs & {r["input"] for r in self.rows["test"]})

    def test_test_rows_carry_no_training_target(self):
        for r in self.rows["test"]:
            self.assertNotIn("target", r)
            self.assertIn("rref", r)

    def test_guard_input_hides_labels_and_effects(self):
        for r in self.rows["train"][:200] + self.rows["test"]:
            for leak in ('"decision"', "R-ref", "Closed Won history", r["family"]):
                self.assertNotIn(leak, r["input"])
            self.assertIn("## Dry run", r["input"])

    def test_targets_cite_rules_for_every_escalation(self):
        for r in self.rows["train"]:
            t = r["target"]
            self.assertEqual(t["decision"] == "ALLOW", not t["rules"] or t["decision"] == "ALLOW", r["id"])

    def test_test_sample_covers_every_policy(self):
        self.assertEqual({r["policy"] for r in self.rows["test"]}, {"lenient", "standard", "strict", "heldout-prose"})
        self.assertEqual(len(self.rows["test"]), sum(dataset.TEST_QUOTAS.values()))


if __name__ == "__main__":
    unittest.main()
