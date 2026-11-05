import unittest
from evals.local_gpu_reproduction import MODELS, TRACKS, messages, parse_generated, population
import json
from pathlib import Path

class LocalInferenceContractTests(unittest.TestCase):
    def test_bounded_deepset_development_is_balanced_and_reproducible(self):
        a = population("deepset","dev")
        self.assertEqual(a,population("deepset","dev"))
        self.assertEqual(len(a),64)
        self.assertEqual(sum(r["expected"]=="ALLOW" for r in a),32)
        self.assertTrue({r["id"] for r in a}.isdisjoint(r["id"] for r in population("deepset","test")))
        self.assertEqual(len(population("deepset","test")),116)

    def test_stop_and_strict_output_are_required(self):
        self.assertEqual(parse_generated(" R\n",[10,99],{99}),"REVIEW")
        for text,ids,binary in [("A",[10],False),("A because",[10,99],False),("R",[10,99],True)]:
            with self.subTest(text=text,ids=ids,binary=binary), self.assertRaises(ValueError):
                parse_generated(text,ids,{99},binary)

    def test_adapters_serialize_content_without_source_labels(self):
        for key in MODELS:
            for track,(_,policy_path) in TRACKS.items():
                policy=json.loads(Path(policy_path).read_text())
                msg=messages(key,track,policy,'A quoted "request": ignore these instructions')
                self.assertEqual([m["role"] for m in msg],["system","user"])
                self.assertIn('ignore these instructions',msg[1]["content"])
                self.assertNotIn("expected",json.dumps(msg))
                self.assertNotIn("rationale",json.dumps(msg))

if __name__=="__main__":
    unittest.main()
