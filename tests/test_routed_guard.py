import unittest
from unittest.mock import Mock,patch
from evals.routed_guard.common import choose_model,choice_request,labels_for,policy_hash,select_mapping,typed_result,report_metrics
from evals.routed_guard.experiment import pilot_cases
from evals.routed_guard.server import Gateway,Request

POLICY=dict(purpose="test",block="prohibited",allow="allowed",review="ambiguous",precedence="clear violation first")

class MandatoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.router=Mock();self.router.predict.return_value=dict(candidate_categories=["hate_speech"],fallback_required=False)
        self.manager=Mock();self.manager.guard.return_value=dict(prediction="ALLOW",model="shieldstral",input_sha256="x",policy_sha256="y")
        self.config=dict(policies={"harmful_requests-v0":POLICY},selection_path="/nonexistent-selection-for-tests")
        self.gateway=Gateway(self.config,self.router,self.manager)

    def test_every_regular_request_runs_router_and_guard(self):
        out=self.gateway.moderate(Request(content="hello"))
        self.router.predict.assert_called_once_with("hello")
        self.manager.guard.assert_called_once_with("shieldstral","hello","harmful_requests-v0")
        self.assertTrue(out["guard_attempted"])

    def test_low_confidence_does_not_bypass_guard(self):
        self.router.predict.return_value=dict(candidate_categories=["hate_speech"],fallback_required=True)
        self.gateway.moderate(Request(content="hello"));self.manager.guard.assert_called_once()

    def test_router_error_still_calls_default_guard(self):
        self.router.predict.side_effect=RuntimeError("router unavailable")
        out=self.gateway.moderate(Request(content="hello"))
        self.assertTrue(out["router_error"]);self.manager.guard.assert_called_once()

    def test_guard_failure_cannot_become_allow_or_successful_review(self):
        self.manager.guard.side_effect=RuntimeError("backend down")
        out=self.gateway.moderate(Request(content="hello"))
        self.assertEqual(out["prediction"],"REVIEW");self.assertEqual(out["status"],"error");self.assertTrue(out["error"])

    def test_policy_remains_caller_configuration(self):
        self.gateway.moderate(Request(content="hello",policy_id="harmful_requests-v0"))
        self.assertEqual(self.manager.guard.call_args.args[2],"harmful_requests-v0")

    def test_direct_model_endpoint_is_a_control_without_router(self):
        self.gateway.moderate(Request(content="hello",model="kev"),forced=True)
        self.router.predict.assert_not_called();self.manager.guard.assert_called_once_with("kev","hello","harmful_requests-v0")

    def test_single_class_benign_panel_keeps_block_possible(self):
        self.assertEqual(labels_for("benign_lookalikes-v0"),("ALLOW","BLOCK"))
        self.assertEqual(labels_for("jailbreak_attempts-v0"),("ALLOW","BLOCK"))

    def test_typed_decision_supports_review(self):
        r=typed_result(["ALLOW","BLOCK","REVIEW"],[0.,1.,3.])
        self.assertEqual(r["prediction"],"REVIEW")
        self.assertAlmostEqual(sum(r["probabilities"].values()),1.)

    def test_native_request_omits_caller_reference_and_ids(self):
        r=choice_request("hello",POLICY,"custom_policy-v0")
        self.assertEqual(r["state"],{"content":"hello"})
        self.assertEqual(set(r["questions"]["moderation"]["criteria"]),{"ALLOW","BLOCK","REVIEW"})

    def test_routing_map_uses_category_or_default(self):
        s=dict(default_model="shieldstral",category_models={"hate_speech":"kev"})
        self.assertEqual(choose_model(dict(candidate_categories=["hate_speech"],fallback_required=False),s)[0],"kev")
        self.assertEqual(choose_model(dict(candidate_categories=["hate_speech"],fallback_required=True),s)[0],"shieldstral")

    def test_unknown_guard_is_rejected(self):
        with self.assertRaises(ValueError):choose_model(None,dict(default_model="unregistered"))

    def test_backend_failure_attempts_default_guard(self):
        selection=dict(default_model="shieldstral",category_models={"hate_speech":"kev"})
        self.manager.guard.side_effect=[RuntimeError("primary failed"),dict(prediction="BLOCK",model="shieldstral")]
        with patch("evals.routed_guard.server.Path.exists",return_value=True),patch("evals.routed_guard.server.read",return_value=selection):
            out=self.gateway.moderate(Request(content="hello"))
        self.assertEqual(out["guard_attempts"],["kev","shieldstral"])
        self.assertEqual(out["status"],"ok")

    def test_failed_review_is_wrong_even_when_reference_is_review(self):
        case=dict(id="x",track="t",expected="REVIEW",input_sha256="i",policy_sha256="p")
        result=dict(id="x",prediction="REVIEW",status="error",error="failed",input_sha256="i",policy_sha256="p")
        report=report_metrics([case],[result],{"t":dict(labels=["REVIEW"],domain="custom_policy")},{})
        self.assertEqual(report["accuracy"],0.)
        self.assertEqual(report["error_rate"],1.)

    def test_pilot_selection_is_deterministic_and_class_balanced(self):
        cases=[dict(id=str(i),track="t",expected="ALLOW" if i%2 else "BLOCK",group=str(i)) for i in range(40)]
        tracks={"t":dict(labels=["ALLOW","BLOCK"])}
        a=pilot_cases(cases,tracks);b=pilot_cases(list(reversed(cases)),tracks)
        self.assertEqual(a,b);self.assertEqual(len(a),8)
        self.assertEqual(sum(r["expected"]=="ALLOW" for r in a),4)

if __name__=="__main__":unittest.main()
