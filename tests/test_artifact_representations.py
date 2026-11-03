import json
import tempfile
import unittest
from pathlib import Path
from evals.artifact_representations.common import rows, predictions, measures, complete
from evals.artifact_representations.policies import candidates

class Contracts(unittest.TestCase):
    def test_unicode_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows.jsonl';p.write_text(json.dumps({'text':'a\u2028b\u0085c'},ensure_ascii=False)+'\n')
            self.assertEqual(len(rows(p)),1)
    def test_threshold_and_metrics(self):
        rr=[{'id':str(i),'expected':y} for i,y in enumerate(['ALLOW','ALLOW','BLOCK','BLOCK'])]
        p=predictions(rr,[.1,.5,.2,.9],'test','test');m=measures(p)
        self.assertEqual((m['false_blocks'],m['missed_threats'],m['balanced_accuracy']),(1,1,.5))
        with self.assertRaises(ValueError): predictions(rr,[.1],'test','test')
        with self.assertRaises(ValueError): predictions(rr,[.1,.2,.3,float('nan')],'test','test')
    def test_complete_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=dict(id='x',expected='ALLOW',group='g',prompt_sha256='h')
            q=p/'metadata/code/test.jsonl';q.parent.mkdir(parents=True);q.write_text(json.dumps(r)+'\n')
            q=p/'predictions/m/code/test/c.jsonl';q.parent.mkdir(parents=True);q.write_text((json.dumps(r)+'\n')*2)
            with self.assertRaises(ValueError): complete(p,'m','code','test','c')
    def test_no_prior_mutation(self):
        previous={p:{k:'' for k in ('purpose','block','allow','precedence','review')} for p in ('brief','structured','evidence')}
        new=candidates(previous)
        self.assertEqual(len(new),6)
        self.assertEqual(previous['structured']['block'],'')
        self.assertIn('normal dependency',new['scope']['allow'])

if __name__=='__main__': unittest.main()
