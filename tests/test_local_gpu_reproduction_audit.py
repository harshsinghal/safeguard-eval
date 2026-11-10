import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.verify_local_gpu_reproduction import verify

BUNDLE=Path(__file__).resolve().parents[1]/"published_runs/2026-11-04-local-5090"

class SavedRecordAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle=Path(self.temp.name)/"bundle"
        shutil.copytree(BUNDLE,self.bundle)

    def test_changed_test_score_is_rejected(self):
        path=self.bundle/"shieldstral-3b/iconography/test/predictions.jsonl"
        rows=[json.loads(x) for x in path.read_text().split("\n") if x]
        rows[0]["score"]+=0.01 if rows[0]["score"]<0.9 else -0.01
        path.write_text("".join(json.dumps(x)+"\n" for x in rows))
        with self.assertRaisesRegex(ValueError,"Score differs"):
            verify(self.bundle)

    def test_changed_test_threshold_is_rejected(self):
        path=self.bundle/"shieldstral-3b/iconography/test/manifest.json"
        manifest=json.loads(path.read_text())
        manifest["thresholds"]=[0.1,0.9]
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,"Test was not bound"):
            verify(self.bundle)

    def test_active_compute_process_fails_cleanup(self):
        path=self.bundle/"cleanup.json"
        cleanup=json.loads(path.read_text())
        cleanup["active_python_gpu_pids"]=["12345"]
        path.write_text(json.dumps(cleanup))
        with self.assertRaisesRegex(ValueError,"GPU cleanup not established"):
            verify(self.bundle)

if __name__=="__main__":
    unittest.main()
