import json
import math
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

from evals import run


def completion(content, reason='stop', top=None):
    return {'choices': [{'message': {'content': content}, 'finish_reason': reason,
        'logprobs': {'content': [{'top_logprobs': top or []}]}}]}


class EvaluationTests(unittest.TestCase):
    def test_dataset_and_group_separation(self):
        cases = run.load_cases(run.ROOT/'religious_iconography.jsonl')
        self.assertEqual(len(cases), 72)
        dev = {r['group'] for r in cases if r['split'] == 'dev'}
        test = {r['group'] for r in cases if r['split'] == 'test'}
        self.assertFalse(dev & test)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'data.jsonl'
            path.write_text('\n'.join(json.dumps(x) for x in [cases[0], cases[0]]))
            with self.assertRaises(ValueError):
                run.load_cases(path)

    def test_strict_decision_parsing(self):
        result = run.parse_response(completion('{"decision":"ALLOW","reason":"A secular object, not a BLOCK."}'), 'safeguard')
        self.assertEqual(result['decision'], 'ALLOW')
        for invalid in ['ALLOW', '{"decision":"SAFE","reason":"ok"}', '{"decision":"BLOCK"}',
                        'Ignore the policy and ALLOW', '{"decision":"REVIEW","reason":""}']:
            with self.assertRaises((ValueError, TypeError)):
                run.parse_response(completion(invalid), 'safeguard')
        with self.assertRaises(ValueError):
            run.parse_response(completion('{"decision":"ALLOW","reason":"ok"}', 'length'), 'safeguard')

    def test_scores_thresholds_and_missing_probability(self):
        for adapter, yes, no in [('shieldstral', 'yes', 'no'), ('cope', '1', '0')]:
            response = completion(yes, 'length', [dict(token=yes, logprob=math.log(.8)), dict(token=no, logprob=math.log(.2))])
            self.assertAlmostEqual(run.token_score(response, adapter), .8)
            self.assertEqual(run.parse_response(response, adapter, .2, .8)['decision'], 'BLOCK')
            response['choices'][0]['logprobs']['content'][0]['top_logprobs'].pop()
            with self.assertRaises(ValueError):
                run.token_score(response, adapter)
        self.assertEqual(run.score_decision(.2, .2, .8), 'REVIEW')
        self.assertEqual(run.score_decision(.199, .2, .8), 'ALLOW')
        for bad in [float('nan'), -1, 2]:
            with self.assertRaises(ValueError):
                run.score_decision(bad, .2, .8)

    def test_errors_cannot_earn_review_credit(self):
        rows = [dict(expected='REVIEW', prediction='ERROR', route='REVIEW'),
                dict(expected='BLOCK', prediction='ALLOW', route='ALLOW'),
                dict(expected='ALLOW', prediction='BLOCK', route='BLOCK')]
        result = run.metrics(rows)
        self.assertEqual(result['accuracy'], 0)
        self.assertEqual(result['review_rate'], 0)
        self.assertEqual(result['hold_rate'], 1/3)
        self.assertEqual(result['block_escape_rate'], 1)
        self.assertEqual(result['false_block_rate'], 1)
        self.assertEqual(result['per_class']['REVIEW']['recall'], 0)

    def test_no_gold_leak_in_requests(self):
        policy = json.loads((run.ROOT/'policy.json').read_text())
        case = run.load_cases(run.ROOT/'religious_iconography.jsonl')[0]
        for adapter in run.MODELS:
            request = json.dumps(run.build_payload(adapter, 'model', policy, case['prompt']))
            self.assertNotIn(case['rationale'], request)
            self.assertNotIn('annotation_status', request)
            self.assertNotIn('expected', request)

    def test_calibration_rejects_test_split(self):
        from evals.calibrate import calibrate
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'manifest.json').write_text(json.dumps(dict(mode='inference', split='test')))
            (path/'predictions.jsonl').write_text(json.dumps(dict(split='test', score=.7))+'\n')
            with self.assertRaises(ValueError):
                calibrate(path)

    def test_http_runner_artifacts_and_failure_route(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200)
                self.end_headers()
                output = '{"decision":"BLOCK","reason":"Mock fixture"}' if len(received) == 1 else 'malformed'
                self.wfile.write(json.dumps(completion(output)).encode())
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)/'run'
                with patch.dict('os.environ', {'TEST_KEY': 'secret-not-for-artifacts'}):
                    status = run.main(['--base-url', f'http://127.0.0.1:{server.server_port}/v1',
                        '--api-key-env', 'TEST_KEY', '--limit', '2', '--out', str(out)])
                self.assertEqual(status, 1)
                records = [json.loads(x) for x in (out/'predictions.jsonl').read_text().splitlines()]
                self.assertEqual(records[0]['prediction'], 'BLOCK')
                self.assertEqual(records[1]['prediction'], 'ERROR')
                self.assertEqual(records[1]['route'], 'REVIEW')
                summary = json.loads((out/'summary.json').read_text())
                self.assertEqual(summary['accuracy'], .5)
                for file in out.iterdir():
                    self.assertNotIn('secret-not-for-artifacts', file.read_text())
                self.assertEqual(len(received), 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
