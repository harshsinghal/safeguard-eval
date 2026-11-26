import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import numpy as np
from evals.competence_router.model import policy_text, policy_contract_hash, encode_pair, probabilities, route, structure
from evals.competence_router.server import Gateway
from evals.competence_router.study import balanced, paired_interval, outcomes
from evals.routed_guard.common import ORDER, MODELS, jsonl
from evals.routed_guard.server import Request

POLICY=dict(purpose='Inspect code',allow='Authorized behavior',block='Theft',review='Missing context',precedence='Judge the artifact',id='private-source-name',source_policy_id='private-id')

class Tokenizer:
    sep_token_id=99
    def __call__(self,text,**kwargs):return {'input_ids':list(range(len(text.split())))}

class FeatureTests(unittest.TestCase):
    def test_policy_features_exclude_source_names_and_accept_real_policy_changes(self):
        text=policy_text(POLICY,('ALLOW','BLOCK'))
        self.assertNotIn('private-source-name',text);self.assertNotIn('private-id',text)
        renamed=dict(POLICY,id='another',source_policy_id='other')
        self.assertEqual(policy_contract_hash(POLICY,('ALLOW','BLOCK')),policy_contract_hash(renamed,('ALLOW','BLOCK')))
        self.assertNotEqual(policy_contract_hash(POLICY,('ALLOW','BLOCK')),policy_contract_hash(dict(POLICY,block='A different rule'),('ALLOW','BLOCK')))
        self.assertNotEqual(policy_contract_hash(POLICY,('ALLOW','BLOCK')),policy_contract_hash(POLICY,('ALLOW','BLOCK','REVIEW')))

    def test_long_prompt_preserves_policy_budget_and_marks_truncation(self):
        ids,trace=encode_pair(Tokenizer(),'word '*1000,POLICY,('ALLOW','BLOCK'))
        self.assertTrue(trace['prompt_truncated']);self.assertEqual(ids[256],99)
        self.assertLessEqual(len(ids),450);self.assertGreater(trace['policy_tokens'],0)

    def test_empty_content_rejected(self):
        with self.assertRaises(ValueError):encode_pair(Tokenizer(),' ',POLICY,('ALLOW','BLOCK'))

    def test_structure_describes_input_only(self):
        self.assertEqual(structure('hello').shape,(10,))
        self.assertGreater(structure('```python\nimport os\n```')[2],structure('hello')[2])

    def test_probabilities_are_independent_not_softmax(self):
        head=dict(mean=[0.,0.],scale=[1.,1.],coef=[[0.,0.]]*4,intercept=[3.]*4)
        p=probabilities(np.array([1.,2.]),head)
        self.assertTrue((p>.9).all());self.assertGreater(p.sum(),3.)

class RouteTests(unittest.TestCase):
    def setUp(self):self.config=dict(default_model='clef',supported_policy_hashes=['known'],enabled_models=['kev','shieldstral'],switch_margin=.05)
    def test_default_wins_ties(self):
        self.assertEqual(route([.8,.8,.8,.8],self.config,'known')[0],'clef')
    def test_margin_requires_real_advantage(self):
        self.assertEqual(route([.2,.8,.2,.78],self.config,'known')[0],'clef')
        self.assertEqual(route([.2,.9,.2,.78],self.config,'known')[0],'shieldstral')
    def test_unsupported_policy_always_defaults(self):
        self.assertEqual(route([0.,1.,0.,.1],self.config,'new')[0],'clef')
    def test_disabled_expert_cannot_be_selected(self):
        self.assertEqual(route([1.,.2,.2,.5],self.config,'known')[0],'clef')
    def test_invalid_distribution_is_rejected(self):
        for values in ([float('nan')]*4,[2.]*4,[.1,.2]):
            with self.assertRaises(ValueError):route(values,self.config,'known')

class MandatoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.router=Mock();self.router.config={'default_model':'clef'}
        self.router.predict.return_value=dict(selected_model='kev',route_reason='competence_route')
        self.manager=Mock();self.manager.guard.return_value=dict(prediction='ALLOW',model='kev')
        self.gateway=Gateway(dict(policies={'harmful_requests-v0':POLICY}),self.router,self.manager)
    def test_model_sees_trusted_policy_and_full_content_reaches_guard(self):
        text='code with context'*1000
        out=self.gateway.moderate(Request(content=text))
        self.router.predict.assert_called_once_with(text,POLICY,('ALLOW','BLOCK'))
        self.manager.guard.assert_called_once_with('kev',text,'harmful_requests-v0')
        self.assertTrue(out['guard_attempted']);self.assertEqual(out['requested_model'],'kev')
    def test_router_error_calls_default(self):
        self.router.predict.side_effect=ValueError('invalid')
        out=self.gateway.moderate(Request(content='hello'))
        self.manager.guard.assert_called_once_with('clef','hello','harmful_requests-v0');self.assertTrue(out['router_error'])
    def test_primary_guard_failure_attempts_default(self):
        self.manager.guard.side_effect=[RuntimeError('failed'),dict(prediction='BLOCK',model='clef')]
        out=self.gateway.moderate(Request(content='hello'))
        self.assertEqual(out['guard_attempts'],['kev','clef']);self.assertEqual(out['status'],'ok')
    def test_all_backends_failed_remains_error_even_for_review(self):
        self.manager.guard.side_effect=RuntimeError('failed')
        out=self.gateway.moderate(Request(content='hello'))
        self.assertEqual(out['status'],'error');self.assertEqual(out['prediction'],'REVIEW');self.assertTrue(out['error'])
    def test_forced_controls_do_not_claim_a_router_call(self):
        out=self.gateway.moderate(Request(content='hello',model='policylm'),forced=True)
        self.router.predict.assert_not_called();self.assertIsNone(out['router']);self.assertEqual(out['route_reason'],'forced_control')
    def test_unknown_policy_fails_before_guard(self):
        with self.assertRaises(ValueError):self.gateway.moderate(Request(content='hello',policy_id='unknown'))
        self.manager.guard.assert_not_called()

class ExperimentTests(unittest.TestCase):
    def test_stratification_is_deterministic_and_caps_group_dominance(self):
        rr=[dict(id=str(i),track='a' if i%2 else 'b',expected='ALLOW' if i%3 else 'BLOCK',group=str(i//4)) for i in range(100)]
        a=balanced(rr,16);b=balanced(list(reversed(rr)),16)
        self.assertEqual(a,b)
        self.assertLessEqual(max(sum(r['group']==g for r in a) for g in {r['group'] for r in a}),2)
        self.assertEqual(len({(r['track'],r['expected']) for r in a}),4)
    def test_bootstrap_treats_identical_group_as_one_cluster(self):
        self.assertEqual(paired_interval([1,1],['g','g']),[1.,1.])
        self.assertEqual(paired_interval([-1,-1],['g','g']),[-1.,-1.])
    def test_targets_allow_multiple_correct_and_mask_technical_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);r=dict(id='x',input_sha256='i',policy_sha256='p',policy_id='harmful_requests-v0')
            jsonl(base/'data/fit.jsonl',[r]);jsonl(base/'public/metadata/fit.jsonl',[dict(r,expected='BLOCK')])
            for m in ORDER:
                p=dict(r,model=m,model_id=MODELS[m]['model'],model_revision=MODELS[m]['revision'],full_input_passed=True,
                    prediction='BLOCK',status='error' if m=='kev' else 'ok')
                jsonl(base/'public/guards/fit'/(m+'.jsonl'),[p])
            _,_,y,mask=outcomes(base,'fit')
            self.assertEqual(y.tolist(),[[1.,1.,0.,1.]])
            self.assertEqual(mask.tolist(),[[True,True,False,True]])
            p['input_sha256']='wrong';jsonl(base/'public/guards/fit'/'clef.jsonl',[p])
            with self.assertRaises(ValueError):outcomes(base,'fit')

if __name__=='__main__':unittest.main()
