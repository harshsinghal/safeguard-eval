import unittest
import tempfile
from pathlib import Path
import numpy as np
from evals.ensemble.common import align,assert_disjoint,partition,metrics
from evals.ensemble.learn import weighted_fit,validity,classify,threshold
from evals.ensemble.common import write,digest
from evals.ensemble.study import verify_freeze,fitting_sources,paired,verify_development


def row(i,score=.4,group=None,expected='ALLOW'):
    return dict(id=str(i),group=group or str(i),prompt_sha256='hash'+str(i),expected=expected,score=score,prediction='ALLOW')


class EnsembleTests(unittest.TestCase):
    def test_alignment_uses_ids_not_file_order(self):
        a=[row(0,.2),row(1,.7,expected='BLOCK')];b=[row(1,.8,expected='BLOCK'),row(0,.3)]
        meta,X,y,valid=align({'a':a,'b':b},['a','b'])
        self.assertEqual([r['id'] for r in meta],['0','1'])
        np.testing.assert_allclose(X,[[.2,.3],[.7,.8]])
        np.testing.assert_equal(y,[0,1]);self.assertTrue(valid.all())

    def test_missing_or_duplicate_examples_cannot_disappear(self):
        with self.assertRaises(ValueError):align({'a':[row(0)],'b':[row(1)]},['a','b'])
        with self.assertRaises(ValueError):align({'a':[row(0),row(0)],'b':[row(0)]},['a','b'])

    def test_mismatched_gold_or_content_rejected(self):
        with self.assertRaises(ValueError):align({'a':[row(0)],'b':[row(0,expected='BLOCK')]},['a','b'])
        with self.assertRaises(ValueError):align({'a':[row(0)],'b':[dict(row(0),prompt_sha256='changed')]},['a','b'])

    def test_failed_member_does_not_become_valid_confidence(self):
        _,X,_,valid=align({'a':[row(0)],'b':[dict(row(0),prediction='ERROR',score=None)]},['a','b'])
        self.assertFalse(valid.all())
        self.assertEqual(classify(np.array([.2]),validity({'kind':'equal-raw'},valid),.5).tolist(),[-1])
        self.assertEqual(classify(X[:,0],validity({'kind':'single-raw','column':0},valid),.5).tolist(),[0])
        with self.assertRaises(ValueError):align({'a':[row(0,float('nan'))]},['a'])

    def test_development_group_and_text_leakage_rejected(self):
        with self.assertRaises(ValueError):assert_disjoint([row(0,group='g')],[row(1,group='g')])
        with self.assertRaises(ValueError):assert_disjoint([row(0)],[dict(row(1),prompt_sha256='hash0')])

    def test_sampling_preserves_groups_and_is_order_invariant(self):
        rr=[row(i,group=str(i//2),expected='BLOCK' if i%4<2 else 'ALLOW') for i in range(1600)]
        a,b=partition(rr,600,400);c,d=partition(list(reversed(rr)),600,400)
        self.assertEqual([r['id'] for r in a],[r['id'] for r in c]);self.assertEqual([r['id'] for r in b],[r['id'] for r in d])
        assert_disjoint(a,b)
        self.assertEqual(len({r['group'] for r in a})*2,len(a))

    def test_weighted_fit_cannot_use_negative_or_unnormalized_weights(self):
        X=np.array([[.05,.8],[.95,.2],[.1,.7],[.9,.3]])
        w,_=weighted_fit(X,np.array([0,1,0,1]),0.)
        self.assertAlmostEqual(w.sum(),1.);self.assertTrue((w>=0).all());self.assertGreater(w[0],.99)

    def test_failures_remain_in_accuracy_and_f1_denominators(self):
        m=metrics([row(0),row(1,expected='BLOCK')],[0,-1])
        self.assertEqual(m['accuracy'],.5);self.assertEqual(m['missed_violations'],1);self.assertEqual(m['errors'],1)

    def test_threshold_tie_is_deterministic(self):
        m=[row(0),row(1,expected='BLOCK')]
        t=threshold(m,np.array([.1,.9]),np.array([True,True]))
        self.assertEqual(t['threshold'],.5)

    def test_frozen_weights_selection_and_data_cannot_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);out=state/'cohorts/demo';out.mkdir(parents=True)
            for p in [out/'models.joblib',out/'selection.json',state/'data-manifest.json',state/'fit.gz']:p.write_text('{}')
            f=dict(cohort='demo',source_hashes=fitting_sources(),models_sha256=digest(out/'models.joblib'),
                selection_sha256=digest(out/'selection.json'),data_manifest_sha256=digest(state/'data-manifest.json'),
                development_hashes={'fit.gz':digest(state/'fit.gz')})
            write(out/'freeze.json',f);verify_freeze(state,'demo')
            for p in [out/'models.joblib',out/'selection.json',state/'data-manifest.json',state/'fit.gz']:
                p.write_text('changed')
                with self.assertRaises(ValueError):verify_freeze(state,'demo')
                p.write_text('{}')

    def test_pre_fit_registration_rejects_changed_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);hs={}
            for split in ['fit','validation']:
                rel=f'scores/wildguard/a/{split}.jsonl.gz';p=state/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}');hs[rel]=digest(p)
            write(state/'data-manifest.json',dict(data_hashes=hs));verify_development(state,'wildguard',['a'])
            (state/'scores/wildguard/a/fit.jsonl.gz').write_text('changed')
            with self.assertRaises(ValueError):verify_development(state,'wildguard',['a'])

    def test_paired_comparison_preserves_direction_and_discordance(self):
        meta=[row(0),row(1,expected='BLOCK'),row(2),row(3,expected='BLOCK')]
        result=paired(meta,np.array([0,1,0,1]),np.array([0,0,1,1]),reps=100)
        self.assertEqual(result['accuracy_delta'],.5);self.assertEqual(result['cases_fixed'],2);self.assertEqual(result['cases_broken'],0)


if __name__=='__main__':unittest.main()
