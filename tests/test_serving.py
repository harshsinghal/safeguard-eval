import unittest
from evals.serving.client import summarize


class ServingMetrics(unittest.TestCase):
    def test_failed_responses_never_inflate_valid_throughput(self):
        rr=[dict(prediction='ALLOW',seconds=.1),dict(prediction='BLOCK',seconds=.3),dict(prediction='ERROR',seconds=.01)]
        m=summarize(rr,2)
        self.assertEqual(m['requests_per_second'],1)
        self.assertEqual(m['errors'],1)
        self.assertAlmostEqual(m['p50_ms'],200)
        self.assertAlmostEqual(m['gpu_usd_per_million'],.8/3600*1e6)

    def test_all_failed_is_not_zero_cost(self):
        m=summarize([dict(prediction='ERROR',seconds=.2)],.2)
        self.assertIsNone(m['gpu_usd_per_million'])
        self.assertIsNone(m['p95_ms'])


if __name__=='__main__':unittest.main()
