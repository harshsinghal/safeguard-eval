"""Keep transfer directions, denominators, and baseline selections unambiguous."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "safeguard-eval"
HELPER = runpy.run_path(str(PACKAGE / "scripts" / "lookup_transfer.py"))


class TransferLookupTests(unittest.TestCase):
    def test_exact_requested_direction_and_error_tradeoff(self):
        result = HELPER["lookup"]("qwen-2b", "policylm")
        self.assertEqual(result["test_n"], 1699)
        self.assertAlmostEqual(result["recipient_initial_policy"]["accuracy_percent"], 85.050029, places=6)
        self.assertAlmostEqual(result["recipient_with_source_selected_policy"]["accuracy_percent"], 81.753973, places=6)
        delta = result["change_transferred_minus_initial"]
        self.assertEqual((delta["false_blocks"], delta["missed_harmful_prompts"], delta["incorrect_total"]), (66, -10, 56))
        reverse = HELPER["lookup"]("policylm", "qwen-2b")
        self.assertGreater(reverse["change_transferred_minus_initial"]["accuracy_percentage_points"], 0)
        self.assertIn("analysis.json", result["sources"]["matrix"])

    def test_every_named_pair_matches_archived_matrix(self):
        archived = json.loads((ROOT / "published_runs" / "2026-10-25-policy-transfer" / "analysis.json").read_text())
        for source, policy in archived["source_selected"].items():
            for recipient, cells in archived["matrix"]["test"].items():
                with self.subTest(source=source, recipient=recipient):
                    result = HELPER["lookup"](source, recipient)
                    self.assertEqual(result["selected_policy_id"], policy)
                    self.assertEqual(result["test_n"], cells[policy]["n"])
                    self.assertAlmostEqual(result["recipient_with_source_selected_policy"]["accuracy_percent"],
                                           cells[policy]["accuracy"] * 100, places=5)

    def test_unchanged_large_model_policy_is_explicit(self):
        for source in ("qwen-4b", "qwen-27b"):
            result = HELPER["lookup"](source, "policylm")
            self.assertTrue(result["source_selected_unchanged_initial_policy"])
            self.assertEqual(result["change_transferred_minus_initial"]["incorrect_total"], 0)

    def test_ambiguous_or_unrecorded_models_are_not_silently_substituted(self):
        for source, recipient in (("qwen", "policylm"), ("qwen-9b", "policylm"), ("policylm", "cope")):
            with self.assertRaises(ValueError):
                HELPER["lookup"](source, recipient)
        completed = subprocess.run([sys.executable, str(PACKAGE / "scripts" / "lookup_transfer.py"),
                                    "--source", "qwen-2b"], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(completed.stdout)

    def test_portable_package_rejects_mismatched_provenance(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "installed"
            shutil.copytree(PACKAGE, target)
            completed = subprocess.run([sys.executable, str(target / "scripts" / "lookup_transfer.py"),
                                        "--source", "qwen-2b", "--recipient", "policylm"],
                                       cwd=name, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(completed.stdout)["recipient_classifier"]["id"], "policylm")
            registry = target / "references" / "sources.json"
            data = json.loads(registry.read_text())
            data["evidence_revision"] = "0" * 40
            registry.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "revisions differ"):
                HELPER["lookup"]("qwen-2b", "policylm", target)


if __name__ == "__main__":
    unittest.main()
