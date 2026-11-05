import unittest
import numpy as np
from evals.liquid_router.common import CATEGORIES,bounded_tokens,rank_candidates
from evals.liquid_router.prepare import purge_overlap
from evals.liquid_router.study import choose_policy,metrics

class LiquidRouterTests(unittest.TestCase):
    def row(self,i,role,text,group=None,category="hate_speech"):
        return dict(id=str(i),role=role,text=text,group=group or str(i),category=category)

    def test_bounded_view_preserves_begin_middle_and_end(self):
        ids=list(range(1000));view=bounded_tokens(ids)
        self.assertEqual(len(view),256);self.assertEqual(view[:96],ids[:96])
        self.assertEqual(view[96:160],ids[468:532]);self.assertEqual(view[-96:],ids[-96:])
        self.assertEqual(bounded_tokens([1,2,3]),[1,2,3])

    def test_held_out_groups_exclude_development(self):
        records=[self.row(1,"fit","some fitting input","shared"),self.row(2,"test","different held out text","shared")]
        kept,audit=purge_overlap(records)
        self.assertEqual([r["id"] for r in kept],["2"]);self.assertEqual(len(audit["excluded"]),1)

    def test_normalized_exact_excludes_cross_category_leakage(self):
        records=[self.row(1,"fit","HELLO   world",category="cyber_safety"),self.row(2,"validation","hello world")]
        kept,_=purge_overlap(records)
        self.assertEqual([r["id"] for r in kept],["2"])

    def test_protected_calibration_never_becomes_fit(self):
        kept,_=purge_overlap([self.row(1,"fit","same"),self.row(2,"protected","same")])
        self.assertEqual([r["role"] for r in kept],["protected"])

    def test_near_duplicate_excludes_fit(self):
        text=" ".join("word"+str(i) for i in range(200))
        kept,audit=purge_overlap([self.row(1,"fit",text),self.row(2,"test",text+" extra")])
        self.assertEqual([r["id"] for r in kept],["2"]);self.assertGreater(audit["near_edges"],0)

    def test_multiple_routes_are_candidates_not_allow(self):
        p=np.arange(1,8,dtype=float);p/=p.sum()
        self.assertEqual(rank_candidates(p,2),CATEGORIES[-1:-3:-1])
        with self.assertRaises(ValueError):rank_candidates(np.zeros(7),2)
        with self.assertRaises(ValueError):rank_candidates(p,0)

    def test_candidate_policy_selected_by_reference_coverage(self):
        records=[dict(category=CATEGORIES[i]) for i in range(7)]
        z=np.eye(7)*8
        policy=choose_policy(records,z)
        self.assertEqual(policy["candidate_count"],1);self.assertTrue(policy["coverage_target_met"])
        z=np.roll(z,1,axis=1)
        policy=choose_policy(records,z)
        self.assertFalse(policy["coverage_target_met"])

    def test_unknown_category_excluded_and_reported(self):
        rr=[dict(category=CATEGORIES[0]),dict(category=None)]
        z=np.zeros((2,7));z[0,0]=1
        report=metrics(rr,z)
        self.assertEqual(report["n"],1);self.assertEqual(report["excluded_unsupported"],1)
        self.assertEqual(report["accuracy"],1.)

    def test_nonfinite_predictions_rejected(self):
        with self.assertRaises(ValueError):metrics([dict(category=CATEGORIES[0])],np.full((1,7),np.nan))

if __name__=="__main__":unittest.main()
