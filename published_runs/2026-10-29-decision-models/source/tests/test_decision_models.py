import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from evals.decision_models.adapters import parse, request
from evals.decision_models.infer import checked_resume
from evals.decision_models.study import candidates, freeze
from evals.jev.study import base_policies, choose_examples
from evals.leaderboard.metrics import select


class DecisionTests(unittest.TestCase):
    def test_native_payload_has_no_gold_or_provenance(self):
        policy=base_policies('hatexplain')['detailed']
        policy['label']='BLOCK'; policy['source']='forbidden_metadata'
        p=request('ordinary text',policy)
        self.assertEqual(p['state'],{'content':'ordinary text'})
        self.assertEqual(set(p['questions']),{'moderation'})
        self.assertNotIn('forbidden_metadata',json.dumps(p))
        self.assertNotIn('label',p['questions']['moderation'])

    def test_head_order_maps_to_named_classes(self):
        a=parse(['BLOCK','ALLOW'],[2.,1.],[.8,.2])
        self.assertEqual((a['score'],a['prediction']),(.8,'BLOCK'))
        self.assertEqual(parse(['BLOCK','ALLOW'],[1.,1.],[.5,.5])['prediction'],'ALLOW')
        for invalid in ([float('nan'),.5],[.8,.8],[-.1,1.1]):
            with self.assertRaises(ValueError): parse(['ALLOW','BLOCK'],[0.,1.],invalid)

    def test_examples_reject_test_data(self):
        with self.assertRaises(ValueError): choose_examples([{'split':'test'}],[{'split':'test'}])

    def test_unresolved_predictions_remain_errors_at_any_cutoff(self):
        c=candidates({'p':[{'prediction':'ERROR','score':None},{'prediction':'BLOCK','score':.9}]})
        selected,grid=select(np.array([0,1]),c)
        self.assertTrue(all(x['unresolved']==1 for x in grid))
        self.assertEqual(selected['balanced']['metrics']['balanced_accuracy'],.5)

    def test_resume_rejects_changed_policy_and_duplicates(self):
        r=dict(id='a',prompt_sha256='p',policy_sha256='old')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'pred.jsonl'; path.write_text(json.dumps(r)+'\n')
            with self.assertRaises(ValueError): checked_resume(path,[r],'new')
            path.write_text((json.dumps(r)+'\n')*2)
            with self.assertRaises(ValueError): checked_resume(path,[r],'old')

    def test_freeze_reads_validation_only(self):
        # A guard fails before any candidate evaluation if a test split is requested.
        def guard(state,slug,ds,split,pid):
            self.assertEqual(split,'validation')
            raise RuntimeError('validation requested')
        with tempfile.TemporaryDirectory() as tmp, patch('evals.decision_models.study.verify'), \
             patch('evals.decision_models.study.verify_policies'), \
             patch('evals.decision_models.study.predictions',side_effect=guard):
            with self.assertRaisesRegex(RuntimeError,'validation requested'): freeze(tmp)

if __name__=='__main__': unittest.main()
