import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from evals.routed_guard.common import read, write
from tools.report_competence_router import package, verify

class EvidenceTests(unittest.TestCase):
    def test_export_only_copies_public_evidence_and_compresses_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=root/'state';bundle=root/'bundle'
            write(state/'public/actual-results.json',dict(accuracy=.5))
            (state/'public/sample.jsonl').write_text('{"id":"opaque"}\n')
            (state/'config.private.json').write_text('SECRET_RUNTIME_PATH')
            (state/'data').mkdir();(state/'data/test.jsonl').write_text('RESTRICTED_PROMPT')
            (state/'checkpoint').mkdir();(state/'checkpoint/weights.bin').write_bytes(b'WEIGHTS')
            with patch('evals.competence_router.study.verify_freeze'),patch('tools.report_competence_router.verify'):
                package(state,bundle)
            self.assertTrue((bundle/'sample.jsonl.gz').exists())
            self.assertFalse((bundle/'config.private.json').exists());self.assertFalse((bundle/'data').exists());self.assertFalse((bundle/'checkpoint').exists())
            self.assertEqual(set(read(bundle/'manifest.json')['files']),{'sample.jsonl.gz','actual-results.json'})
    def test_hash_tampering_fails_before_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'results.json').write_text('{}')
            write(p/'manifest.json',dict(files={'results.json':'bad'}))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify(p)
    def test_incomplete_bundle_cannot_be_misrepresented_as_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);write(p/'manifest.json',dict(files={}))
            with self.assertRaisesRegex(ValueError,'required evidence'):verify(p)

if __name__=='__main__':unittest.main()
