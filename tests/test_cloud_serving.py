import unittest
import httpx
from evals.serving.cloud_lengths import Client, summary
from evals.serving.cloud_shield_smoke import normalized_score


class CloudServingContract(unittest.TestCase):
    def response(self, tokens=3, text='A', finish='stop'):
        return dict(choices=[dict(text=text, finish_reason=finish)],
                    usage=dict(prompt_tokens=tokens, completion_tokens=2))

    def request(self, response):
        client = Client('test-model')
        client.http.close()
        client.http = httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=response)))
        result = client.one(dict(id='case', token_ids=[1,2,3], full_tokens=3))
        client.http.close()
        return result

    def test_changed_token_count_invalidates_measurement(self):
        self.assertEqual(self.request(self.response())['prediction'], 'ALLOW')
        self.assertEqual(self.request(self.response(tokens=4))['prediction'], 'ERROR')

    def test_truncated_or_non_label_outputs_are_errors(self):
        for response in [self.response(text='A because it is safe'),
                         self.response(finish='length'), self.response(text='')]:
            self.assertEqual(self.request(response)['prediction'], 'ERROR')

    def test_errors_do_not_improve_goodput(self):
        m = summary([dict(prediction='ERROR', seconds=.01),
                     dict(prediction='ALLOW', seconds=.1)], 2, hourly_rate=.59)
        self.assertEqual(m['requests_per_second'], .5)
        self.assertEqual(m['errors'], 1)
        self.assertAlmostEqual(m['gpu_usd_per_million'], .59/3600/.5*1e6)

    def test_score_contract_preserves_alternatives_and_rejects_missing_mass(self):
        self.assertAlmostEqual(normalized_score([('yes',-1001),(' no',-1001)]),.5)
        self.assertAlmostEqual(normalized_score([('yes',-1001),(' yes',-1002),('no',-1001)]),.5)
        with self.assertRaises(ValueError): normalized_score([('yes',-.01)])


if __name__=='__main__': unittest.main()
