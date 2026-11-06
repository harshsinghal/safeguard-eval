import unittest
from tools.verify_routed_guard_evidence import verify_route
from evals.routed_guard.common import MODELS

class RoutedTraceTests(unittest.TestCase):
    def setUp(self):
        self.selection=dict(default_model="shieldstral",category_models={"hate_speech":"kev"})
        self.row=dict(status="ok",guard_attempted=True,full_input_passed=True,
            router=dict(candidate_categories=["hate_speech"],fallback_required=False),router_error=False,
            requested_model="kev",guard_attempts=["kev"],model="kev",model_revision=MODELS["kev"]["revision"],selection_status="frozen")
    def test_real_guard_trace_is_consistent(self):
        self.assertTrue(verify_route(self.row,self.selection))
    def test_success_without_guard_rejected(self):
        self.row["guard_attempted"]=False
        with self.assertRaises(ValueError):verify_route(self.row,self.selection)
    def test_wrong_route_rejected(self):
        self.row["requested_model"]="shieldstral"
        with self.assertRaises(ValueError):verify_route(self.row,self.selection)
    def test_failed_allow_rejected(self):
        self.row.update(status="error",prediction="ALLOW")
        with self.assertRaises(ValueError):verify_route(self.row,self.selection)
    def test_failed_review_preserved_as_failure(self):
        self.row.update(status="error",prediction="REVIEW")
        self.assertFalse(verify_route(self.row,self.selection))

if __name__=="__main__":unittest.main()
