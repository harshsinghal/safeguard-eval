import json,tempfile,unittest
from pathlib import Path
from evals.run import load_cases,build_payload,score_decision
from evals.injection.calibration import binary_metrics,calibrate_binary

class InjectionTests(unittest.TestCase):
    def test_no_image_assumptions_or_gold_in_payload(self):
        policy=json.loads(Path('evals/injection/policy.json').read_text())
        for adapter in ('safeguard','cope','shieldstral'):
            payload=build_payload(adapter,'test',policy,'untrusted sample')
            text=json.dumps(payload)
            self.assertNotIn('requested image',text)
            self.assertNotIn('image_prompt',text)
            self.assertIn('untrusted sample',text)
    def test_binary_scoring_penalizes_abstention(self):
        rows=[dict(expected='ALLOW',prediction='ALLOW'),dict(expected='BLOCK',prediction='REVIEW')]
        self.assertAlmostEqual(binary_metrics(rows),.5)
        self.assertEqual(score_decision(.5,.5,.5),'BLOCK')
        self.assertEqual(score_decision(.49,.5,.5),'ALLOW')
    def test_data_integrity(self):
        rows=load_cases('evals/injection/challenge.jsonl')
        self.assertEqual(len(rows),100)
        self.assertEqual(sum(r['split']=='test' for r in rows),80)
        self.assertEqual(len(load_cases('evals/injection/deepset.jsonl')),657)
    def test_binary_calibration_uses_dev_and_rejects_test(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);m=dict(split='dev',mode='inference',selected_ids=['a','b'])
            rows=[dict(id='a',split='dev',expected='ALLOW',score=.2),dict(id='b',split='dev',expected='BLOCK',score=.8)]
            (p/'manifest.json').write_text(json.dumps(m));(p/'predictions.jsonl').write_text('\n'.join(map(json.dumps,rows)))
            self.assertEqual(calibrate_binary(p)['selected']['threshold'],.5)
            m['split']='test';(p/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):calibrate_binary(p)
