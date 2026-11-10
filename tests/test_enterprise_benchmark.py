import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from evals.enterprise_benchmark.registry import TRACKS,PROFILES,case_id
from evals.enterprise_benchmark.sources import sha
from evals.enterprise_benchmark.build import group_and_filter,choose
from evals.enterprise_benchmark.scoring import score,item_weights,compare,track_metrics

def row(uid="one",track="agent_actions",split="evaluation",label="ALLOW",text="A scoped operation",group="g"):
    return dict(id=uid,source_id=uid,track=track,split=split,expected=label,source_group=group,
        prompt=text,input_sha256=sha(text),source_metadata={})

class GroupingTests(unittest.TestCase):
    def test_model_facing_ids_do_not_echo_reference_labels(self):
        opaque=case_id("custom_policy","ri-01-BLOCK")
        self.assertRegex(opaque,r"^ems-[0-9a-f]{24}$")
        self.assertNotIn("BLOCK",opaque)
        self.assertEqual(opaque,case_id("custom_policy","ri-01-BLOCK"))

    def test_action_run_family_cannot_cross_roles(self):
        a=row("a",split="calibration",text="context A")
        b=row("b",track="agent_runs",text="context B")
        kept,audit=group_and_filter([a,b])
        self.assertEqual([r["id"] for r in kept],["b"])
        self.assertEqual(audit["exclusions"][0]["reason"],"group_overlaps_evaluation")

    def test_same_text_can_have_different_policy_labels(self):
        a=row("a",track="harmful_requests",label="BLOCK")
        b=row("b",track="injection_deepset",label="ALLOW")
        kept,_=group_and_filter([a,b])
        self.assertEqual(len(kept),2)
        self.assertEqual(kept[0]["group"],kept[1]["group"])

    def test_conflicting_exact_labels_within_task_are_quarantined(self):
        kept,audit=group_and_filter([row("a"),row("b",label="BLOCK")])
        self.assertEqual(kept,[])
        self.assertEqual(len(audit["exclusions"]),2)

    def test_model_results_are_prohibited_selector_inputs(self):
        with self.assertRaisesRegex(ValueError,"model outputs"):
            group_and_filter([dict(row(),prediction="ALLOW")])

    def test_input_hash_drift_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"input drift"):
            group_and_filter([dict(row(),prompt="changed")])

    def test_canonical_selection_survives_pool_reordering(self):
        rr=[row(str(i),text=f"operation {i}",group=str(i),label="ALLOW" if i<6 else "BLOCK") for i in range(12)]
        rr,_=group_and_filter(rr)
        vec=np.random.default_rng(1).normal(size=(12,4)).astype(np.float32)
        assignment={r["id"]:i%3 for i,r in enumerate(rr)}
        distance={r["id"]:float(i)/12 for i,r in enumerate(rr)}
        a=choose(rr,vec,assignment,distance,"agent_actions","evaluation",8)[0]
        b=choose(rr[::-1],vec[::-1],assignment,distance,"agent_actions","evaluation",8)[0]
        self.assertEqual([r["id"] for r in a],[r["id"] for r in b])

class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.cases=[]
        for task,spec in TRACKS.items():
            for label in spec["labels"]:
                uid=task+"::"+label
                self.cases.append(dict(id=uid,source_id=uid,track=task,expected=label,input_sha256=sha(uid),
                    policy_sha256=sha(task),policy_id=task+"-v0",group=uid))
        self.write_bundle()

    def write_bundle(self):
        blobs={"calibration.jsonl":"","evaluation.jsonl":"".join(json.dumps(r)+"\n" for r in self.cases),
               "tracks.json":json.dumps(TRACKS),"profiles.json":json.dumps(PROFILES)}
        for name,text in blobs.items():(self.root/name).write_text(text)
        manifest=dict(version="test",files={n:sha((self.root/n).read_bytes()) for n in blobs},missing_tracks=[])
        (self.root/"manifest.json").write_text(json.dumps(manifest))

    def predictions(self,label=None):
        return [dict(id=r["id"],prediction=label or r["expected"],input_sha256=r["input_sha256"],policy_sha256=r["policy_sha256"]) for r in self.cases]

    def test_perfect_predictions_score_100(self):
        result=score(self.root,self.predictions())
        self.assertEqual(result["accuracy"],1)
        for value in result["profiles"].values():self.assertAlmostEqual(value,100)

    def test_missing_outputs_are_wrong_and_never_dropped(self):
        result=score(self.root,[])
        self.assertEqual(result["n"],len(self.cases))
        self.assertEqual(result["missing_outputs"],len(self.cases))
        self.assertEqual(result["accuracy"],0)
        self.assertTrue(all(v==0 for v in result["profiles"].values()))

    def test_profile_weights_sum_to_one(self):
        weights=item_weights(self.cases,TRACKS,PROFILES)
        for p in PROFILES:self.assertAlmostEqual(sum(r[p] for r in weights.values()),1)

    def test_large_benign_stratum_cannot_dominate_macro_score(self):
        original=score(self.root,self.predictions("ALLOW"))
        allow=next(r for r in self.cases if r["track"]=="harmful_requests" and r["expected"]=="ALLOW")
        self.cases += [dict(allow,id="extra"+str(i)) for i in range(30)]
        self.write_bundle()
        larger=score(self.root,self.predictions("ALLOW"))
        self.assertGreater(larger["accuracy"],original["accuracy"])
        for p in PROFILES:self.assertAlmostEqual(larger["profiles"][p],original["profiles"][p])

    def test_agent_task_has_declared_higher_enterprise_weight(self):
        weights=item_weights(self.cases,TRACKS,PROFILES)
        self.assertAlmostEqual(weights["agent_actions::BLOCK"]["enterprise_reference_v0"]/
            weights["harmful_requests::BLOCK"]["enterprise_reference_v0"],7)

    def test_missing_reference_task_withholds_headline(self):
        self.cases=[r for r in self.cases if r["track"]!="source_code"];self.write_bundle()
        result=score(self.root,self.predictions())
        self.assertTrue(all(v is None for v in result["profiles"].values()))

    def test_single_class_panels_do_not_claim_balanced_accuracy(self):
        result=score(self.root,self.predictions())
        self.assertIsNone(result["tasks"]["benign_lookalikes"]["balanced_accuracy"])
        self.assertIsNone(result["tasks"]["jailbreak_attempts"]["balanced_accuracy"])

    def test_duplicate_unknown_and_unbound_predictions_rejected(self):
        pred=self.predictions()
        for changed,pattern in [(pred+[pred[0]],"Duplicate"),([dict(pred[0],id="unknown")],"Unknown"),
                                ([dict(pred[0],input_sha256="wrong")],"hash")]:
            with self.subTest(pattern=pattern),self.assertRaisesRegex(ValueError,pattern):
                score(self.root,changed)

    def test_review_cannot_earn_credit_on_binary_tasks(self):
        result=score(self.root,self.predictions("REVIEW"))
        self.assertEqual(result["tasks"]["agent_actions"]["accuracy"],0)
        self.assertGreater(result["tasks"]["agent_actions"]["out_of_contract_review"],0)

    def test_status_error_overrides_a_label(self):
        pred=self.predictions();pred[0]["status"]="error"
        result=score(self.root,pred)
        self.assertEqual(result["tasks"][self.cases[0]["track"]]["correct"],
            len(TRACKS[self.cases[0]["track"]]["labels"])-1)

    def test_paired_changes_use_the_same_error_handling_as_scores(self):
        baseline=self.predictions();candidate=copy.deepcopy(baseline);candidate[0]["status"]="error"
        result=compare(self.root,baseline,candidate)
        self.assertEqual(result["paired_changes"][self.cases[0]["track"]]["newly_wrong"],1)

    def test_private_export_omits_all_reference_fields(self):
        from tools.export_enterprise_inputs import export
        state=self.root/"private-state";state.mkdir()
        pool=[dict(id=r["track"]+"::"+r["source_id"],prompt=r["id"],expected=r["expected"]) for r in self.cases]
        (state/"pool.jsonl").write_text("".join(json.dumps(r)+"\n" for r in pool))
        out=self.root/"inputs"
        export(self.root,state,out)
        exported=[json.loads(x) for x in (out/"evaluation.jsonl").read_text().split("\n") if x]
        self.assertEqual(len(exported),len(self.cases))
        for r in exported:self.assertEqual(set(r),{"id","policy_id","content","input_sha256","policy_sha256"})

    def test_manifest_path_traversal_rejected(self):
        manifest=json.loads((self.root/"manifest.json").read_text());manifest["files"]["../private"]="x"
        (self.root/"manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):score(self.root,self.predictions())

if __name__=="__main__":unittest.main()
