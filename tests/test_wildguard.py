import json
from pathlib import Path
import tempfile
import unittest

from evals.wildguard.data import sample, split_groups, normalized
from evals.wildguard.metrics import metrics, calibrate, paired_interval
from evals.wildguard.run import payload, parse, validate_freeze

class WildGuardTests(unittest.TestCase):
    def test_payload_prompt_only_and_binary(self):
        policy=json.loads(Path('evals/wildguard/policies/p0.json').read_text())
        text='Test a quoted instruction.'
        for adapter in ('safeguard','cope','shieldstral','wildguard'):
            p=payload(adapter,'model',policy,text)
            self.assertIn(text,json.dumps(p))
            for forbidden in ('prompt_harm_label','expected','adversarial','subcategory'):
                self.assertNotIn('"'+forbidden+'"',json.dumps(p))
        p=payload('wildguard','model',None,text)
        self.assertIn('AI assistant:\n\n\n---',p['prompt'])
        self.assertTrue(p['add_special_tokens'])
        self.assertFalse(p['prompt'].startswith('<s>'))
        self.assertNotIn('or REVIEW',payload('safeguard','model',policy,text)['messages'][0]['content'])

    def test_official_three_line_parser_and_errors(self):
        def response(text):return {'choices':[{'finish_reason':'stop','text':text}]}
        self.assertEqual(parse(response('Harmful request: yes\nResponse refusal: n/a\nHarmful response: n/a'),'wildguard')['prediction'],'BLOCK')
        for text in ['Harmful request: no','Harmful request: no\nResponse refusal: maybe\nHarmful response: no']:
            with self.assertRaises(ValueError):parse(response(text),'wildguard')
        with self.assertRaises(ValueError):parse({'choices':[{'finish_reason':'length','message':{'content':'{"decision":"BLOCK","reason":"x"}'}}]},'safeguard')

    def test_failures_count_incorrect_and_official_f1(self):
        rows=[{'expected':'ALLOW','prediction':'ERROR'},{'expected':'BLOCK','prediction':'BLOCK'}]
        r=metrics(rows)
        self.assertEqual(r['accuracy'],.5);self.assertEqual(r['errors'],1)
        self.assertAlmostEqual(r['official_harmful_f1'],2/3)
        self.assertEqual(r['harmful_f1'],1.)

    def test_calibration_rejects_non_validation(self):
        with self.assertRaises(ValueError):calibrate([dict(split='test',score=.8,prediction='BLOCK',expected='BLOCK')])
        c=calibrate([dict(split='validation',score=.8,prediction='BLOCK',expected='BLOCK'),dict(split='validation',score=.2,prediction='ALLOW',expected='ALLOW')])
        self.assertEqual(c['selected']['threshold'],.5)

    def test_group_split_and_sampling_reproducibility(self):
        rows=[dict(id=str(i),group=str(i//2),expected='BLOCK' if i%2 else 'ALLOW',adversarial=False,subcategory='x') for i in range(200)]
        split_groups(rows)
        self.assertEqual(len({r['split'] for r in rows}),3)
        for i in range(100):self.assertEqual(len({r['split'] for r in rows if r['group']==str(i)}),1)
        self.assertEqual([r['id'] for r in sample(rows,20)],[r['id'] for r in sample(list(reversed(rows)),20)])
        self.assertEqual(normalized('Ａ  B'),'a b')

    def test_paired_alignment(self):
        a=[dict(id='1',group='g',expected='BLOCK',prediction='BLOCK')]
        b=[dict(id='1',group='g',expected='BLOCK',prediction='ALLOW')]
        self.assertEqual(paired_interval(a,b,reps=100)['ci95'],[1.,1.])
        with self.assertRaises(ValueError):paired_interval(a,[dict(b[0],id='2')])

    def test_holdout_requires_freeze(self):
        with self.assertRaises(ValueError):validate_freeze(None,'wildguard',None,'revision')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'freeze.json';p.write_text('{"status":"draft"}')
            with self.assertRaises(ValueError):validate_freeze(p,'wildguard',None,'revision')

if __name__=='__main__':unittest.main()
