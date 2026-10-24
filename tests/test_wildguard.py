import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from evals.wildguard.data import sample, split_groups, normalized
from evals.wildguard.metrics import metrics, calibrate, paired_interval
from evals.wildguard.study import select, POLICY_MODELS
from evals.wildguard.run import payload, parse, validate_freeze, read_rows, run, digest

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

    def test_jsonl_preserves_unicode_line_separators(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.jsonl'
            row=dict(id='x',expected='ALLOW',split='fit',prompt='first\u2028second\u0085third')
            p.write_text(json.dumps(row,ensure_ascii=False)+'\n')
            self.assertEqual(read_rows(p)[0]['prompt'],row['prompt'])

    def test_runner_retains_failures_and_excludes_prompts_from_predictions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=root/'data.jsonl'
            rows=[dict(id=str(i),group=str(i),prompt='private source '+str(i),expected='BLOCK',split='fit',adversarial=False,subcategory='x') for i in range(2)]
            data.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            args=SimpleNamespace(data=data,stage='pilot',policy=Path('evals/wildguard/policies/p0.json'),adapter='safeguard',revision='r',freeze=None,max_tokens=4096,concurrency=1,base='http://127.0.0.1:8000',out=root/'out',model='model')
            calls=[]
            def fake_post(base,path,body):
                calls.append(body)
                return {'choices':[dict(finish_reason='stop' if len(calls)==1 else 'length',message={'content':'{"decision":"BLOCK","reason":"rule applies"}'})]}
            with patch('evals.wildguard.run.post',fake_post):result=run(args)
            self.assertEqual(result['n'],2);self.assertEqual(result['accuracy'],.5);self.assertEqual(result['errors'],1)
            self.assertNotIn('private source',(args.out/'predictions.jsonl').read_text())
            self.assertIn('private source',(args.out/'private-raw.jsonl').read_text())
            self.assertNotIn('expected',json.dumps(calls))
            with self.assertRaises(FileExistsError):run(args)

    def test_selection_requires_matched_data_and_immutable_policies(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);candidates=[]
            for version in ('p0','p1'):
                policy=root/(version+'.json');policy.write_text(json.dumps(dict(id=version,block='harm')))
                c=dict(path=policy.name,sha256=digest(policy),scope='initial' if version=='p0' else 'shared',runs={})
                for adapter in POLICY_MODELS:
                    c['runs'][adapter]={}
                    for split in ('fit','validation'):
                        name=f'{adapter}-{version}-{split}';folder=root/name;folder.mkdir()
                        c['runs'][adapter][split]=name
                        rows=[dict(id=split+str(i),group=str(i),expected=label,prediction=label if version=='p1' else 'ALLOW',split=split) for i,label in enumerate(('ALLOW','BLOCK'))]
                        (folder/'manifest.json').write_text(json.dumps(dict(split=split,adapter=adapter,policy_sha256=digest(policy),ids=[r['id'] for r in rows],dataset_sha256=split)))
                        (folder/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
                candidates.append(c)
            registry=root/'registry.json';registry.write_text(json.dumps(dict(candidates=candidates)))
            result=select(registry,root)
            self.assertEqual(result['shared'],'p1')
            self.assertEqual(set(result['individual'].values()),{'p1'})
            bad=root/'policylm-p1-validation'/'manifest.json';m=json.loads(bad.read_text());m['dataset_sha256']='changed';bad.write_text(json.dumps(m))
            with self.assertRaises(ValueError):select(registry,root)
            m['dataset_sha256']='validation';bad.write_text(json.dumps(m))
            (root/'p1.json').write_text('{"id":"changed"}')
            with self.assertRaises(ValueError):select(registry,root)

    def test_holdout_requires_freeze(self):
        with self.assertRaises(ValueError):validate_freeze(None,'wildguard',None,'revision')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'freeze.json';p.write_text('{"status":"draft"}')
            with self.assertRaises(ValueError):validate_freeze(p,'wildguard',None,'revision')

if __name__=='__main__':unittest.main()
