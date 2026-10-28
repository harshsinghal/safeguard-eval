import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.special import expit,log_softmax

from evals.ensemble.common import write,digest
from evals.ensemble.learn import classify,validity
from evals.ensemble_logits.learn import log_odds,predict,search
from evals.ensemble_logits.study import source_hashes,verify_freeze,stage_test


class LogOddsTests(unittest.TestCase):
    def test_inverse_and_margin_identity(self):
        margins=np.array([-18.,-2.,0.,2.,18.])
        np.testing.assert_allclose(log_odds(expit(margins)),margins,atol=2e-8)
        logits=np.array([[2.,4.,-1.],[1002.,1004.,999.]])
        lp=log_softmax(logits,axis=1)
        p=expit(lp[:,1]-lp[:,0])
        np.testing.assert_allclose(log_odds(p),logits[:,1]-logits[:,0])

    def test_boundary_nonfinite_and_outside_scores_rejected(self):
        for value in [0.,1.,-0.1,1.1,np.nan,np.inf]:
            with self.assertRaises(ValueError):log_odds([[.3,value]])

    def test_averaging_conflicting_equal_margins_is_neutral(self):
        result=predict({'kind':'logit-equal'},np.array([[.1,.9],[.9,.9]]))
        np.testing.assert_allclose(result,[.5,.9])

    def test_failed_member_stays_failed(self):
        scores=np.array([[.3,.5]]);valid=np.array([[True,False]])
        c={'kind':'logit-equal'}
        self.assertEqual(classify(predict(c,scores),validity(c,valid),.5).tolist(),[-1])
        self.assertEqual(validity({'kind':'single-logit','column':0},valid).tolist(),[True])

    def test_scaling_only_training_and_individual_ignores_other_failure(self):
        X=np.array([[.1,.2],[.2,.8],[.8,.4],[.9,.5],[.3,.3],[.7,.6]])
        y=np.array([0,0,1,1,0,1]);valid=np.ones_like(X,dtype=bool);valid[3,1]=False
        vm=[dict(expected='BLOCK'),dict(expected='ALLOW')]
        V=np.array([[.999,.999],[.001,.001]]);vv=np.ones_like(V,dtype=bool)
        old={'candidates':[], 'primary':'old/logistic','best_single':'old/single','best_ensemble':'old/ensemble'}
        new,selected=search(['a','b'],X,y,valid,vm,V,vv,old)
        stack=next(c for c in new if c['kind']=='logit-logistic')
        own=next(c for c in new if c['id']=='logit-single/a/C0.01')
        np.testing.assert_allclose(stack['model'].steps[0][1].mean_,log_odds(X[valid.all(axis=1)]).mean(axis=0))
        np.testing.assert_allclose(own['model'].steps[0][1].mean_,[log_odds(X[:,0]).mean()])
        self.assertEqual(selected['fitting_rows'],5)
        self.assertEqual(len(new),16)
        self.assertEqual(set(selected['selected']['per_model']),{'a','b'})

    def test_frozen_new_selection_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);out=state/'cohorts/demo';out.mkdir(parents=True)
            for name in ['models.joblib','selection.json']:(out/name).write_text('{}')
            write(state/'registration.json',dict(source_hashes=source_hashes(),input_hashes={}))
            write(out/'freeze.json',dict(cohort='demo',registration_sha256=digest(state/'registration.json'),source_hashes=source_hashes(),
                models_sha256=digest(out/'models.joblib'),selection_sha256=digest(out/'selection.json')))
            verify_freeze(state,'demo');(out/'selection.json').write_text('changed')
            with self.assertRaises(ValueError):verify_freeze(state,'demo')

    def test_test_staging_requires_all_cohorts_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('evals.ensemble_logits.study.verify_registration',return_value={}):
                with patch('evals.ensemble_logits.study.verify_freeze',side_effect=ValueError('Missing freeze')):
                    with self.assertRaises(ValueError):stage_test(tmp,tmp)
            self.assertFalse((Path(tmp)/'test-staging.json').exists())


if __name__=='__main__':unittest.main()
