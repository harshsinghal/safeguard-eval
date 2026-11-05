import unittest
from pathlib import Path
from tools.verify_liquid_router_evidence import safe_relative

class ArtifactPathTests(unittest.TestCase):
    def test_nested_relative_path(self):
        self.assertEqual(safe_relative("metadata/test.jsonl.gz"),Path("metadata/test.jsonl.gz"))
    def test_parent_traversal_rejected(self):
        for value in ("../outside","metadata/../../outside"):
            with self.assertRaises(ValueError):safe_relative(value)
    def test_absolute_or_empty_rejected(self):
        for value in ("/tmp/outside",""):
            with self.assertRaises(ValueError):safe_relative(value)

if __name__=="__main__":unittest.main()
