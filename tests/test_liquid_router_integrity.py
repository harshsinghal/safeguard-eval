import unittest
from tools.verify_liquid_router_inputs import verify_cohort
from evals.liquid_router.common import sha

class CohortIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.fixed=[dict(track="hate_speech",source_id="x",input_sha256=sha("hello"),expected="ALLOW")]
        self.actual=[dict(self.fixed[0],text="hello",category="hate_speech")]

    def test_original_cohort_passes(self):
        self.assertEqual(verify_cohort(self.actual,self.fixed),1)

    def test_rehashed_cache_cannot_replace_frozen_text(self):
        self.actual[0].update(text="changed",input_sha256=sha("changed"))
        with self.assertRaisesRegex(ValueError,"cohort drift"):verify_cohort(self.actual,self.fixed)

    def test_reference_decision_drift_rejected(self):
        self.actual[0]["expected"]="BLOCK"
        with self.assertRaises(ValueError):verify_cohort(self.actual,self.fixed)

    def test_unsupported_policy_is_not_a_known_category(self):
        fixed=[dict(self.fixed[0],track="custom_policy")]
        actual=[dict(fixed[0],text="hello",category="harmful_requests")]
        with self.assertRaisesRegex(ValueError,"category drift"):verify_cohort(actual,fixed)

    def test_duplicate_case_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):verify_cohort(self.actual*2,self.fixed)

if __name__=="__main__":unittest.main()
