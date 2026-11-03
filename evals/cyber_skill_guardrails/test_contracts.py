import tempfile
import unittest
from pathlib import Path
from .common import *
from .data import family, inventory, partition
from .infer import jobs, record, runs
from .report import intervals

class Contracts(unittest.TestCase):
    def test_json_lines_and_metadata(self):
        with tempfile.TemporaryDirectory() as t:
            r={'id':'a','prompt':'a\u2028b\nline','skill_text':'private','expected':'ALLOW'}
            jsonl(Path(t)/'x.jsonl',[r])
            self.assertEqual(rows(Path(t)/'x.jsonl'),[r])
            self.assertNotIn('prompt',meta(r));self.assertNotIn('skill_text',meta(r))
    def test_grouped_balanced_partition(self):
        rr=[dict(id=str(i),group=str(i//4),expected='BLOCK' if i%2 else 'ALLOW') for i in range(100)]
        ss=partition(rr,dict(fit=32,validation=16,test=16))
        for a,b in [('fit','validation'),('fit','test'),('validation','test')]:
            self.assertFalse({r['group'] for r in ss[a]}&{r['group'] for r in ss[b]})
        for x in ss.values():self.assertEqual(sum(r['expected']=='BLOCK' for r in x)*2,len(x))
    def test_family_and_inventory(self):
        self.assertEqual(family('clean-tool__PI_B12'),family('clean-tool'))
        inv=inventory('GENERATED tool <- generated_malicious/PI/B4/a\nWILD x <- wild_malware/author/name')
        self.assertEqual(inv['tool']['vector'],'PI');self.assertEqual(inv['x']['author'],'author')
    def test_input_view_and_cache_binding(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t);r=dict(id='x',prompt='package',skill_text='document',prompt_sha256=hash_value('package'),
                skill_text_sha256=hash_value('document'),expected='BLOCK',group='g')
            jsonl(state/'data/skills/test.jsonl',[r])
            path,jj,n=jobs(state,'qwen','skills','test','brief',{},'package')
            self.assertEqual(jj[0]['body']['content'],'package');self.assertNotIn('expected',jj[0]['body'])
            jsonl(path,[record(jj[0],dict(prediction='BLOCK',score=.8),'qwen')])
            self.assertEqual(jobs(state,'qwen','skills','test','brief',{},'package')[1],[])
            with self.assertRaisesRegex(ValueError,'Cache request changed'):
                jobs(state,'qwen','skills','test','brief',{},'skill_only')
    def test_test_requires_freeze(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t);write(state/'policies/cyber/qwen.json',{'brief':{}})
            with self.assertRaises(FileNotFoundError):runs(state,'qwen','cyber','test')
    def test_paired_identical_and_error_denominators(self):
        rr=[dict(id='a',group='a',expected='ALLOW',prediction='ERROR'),
            dict(id='b',group='b',expected='BLOCK',prediction='BLOCK')]
        self.assertEqual(measures(rr)['balanced_accuracy'],.5)
        self.assertEqual(measures(rr)['unresolved'],1)
        self.assertEqual(intervals(rr,rr)['delta_ci95'],[0.,0.])

if __name__=='__main__':unittest.main()
