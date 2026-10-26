import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals.policy_transfer import author, common, run, study
from evals.qwen_policy import run as qwen
from evals.wildguard import run as specialist


class TransferTests(unittest.TestCase):
    def case(self, i=0, split='fit'):
        return dict(id=str(i), split=split, group=str(i), expected='BLOCK',
                    prompt='A request that is treated as data.', subcategory='example')

    def test_editor_rejects_nonfitting_or_misaligned_feedback(self):
        row=self.case(); pred=dict(row, prediction='ALLOW'); del pred['prompt']
        with self.assertRaises(ValueError):
            author.feedback([dict(row, split='test')], [pred])
        with self.assertRaises(ValueError):
            author.feedback([row], [dict(pred, expected='ALLOW')])
        with self.assertRaises(ValueError):
            author.feedback([row], [pred, pred])
        examples, ids=author.feedback([row], [pred])
        self.assertEqual(ids, ['0'])
        self.assertEqual(set(examples[0]), {'request','excerpt_truncated','expected','predicted'})

    def test_feedback_is_deterministic_bounded_and_marks_excerpt(self):
        rows=[dict(self.case(i), prompt='x'*1300) for i in range(40)]
        preds=[dict(r, prediction='ALLOW') for r in rows]
        a=author.feedback(rows, preds)
        b=author.feedback(list(reversed(rows)), list(reversed(preds)))
        self.assertEqual(a,b); self.assertEqual(len(a[0]),32)
        self.assertTrue(all(x['excerpt_truncated'] and len(x['request'])==1200 for x in a[0]))

    def test_editor_preserves_scaffold_and_rejects_copied_passage(self):
        base=common.read(common.BASE)
        edit={k:base[k] for k in common.EDITABLE}
        p=author.validate_edit(edit, [], 'candidate')
        self.assertEqual(p['purpose'],base['purpose'])
        with self.assertRaises(ValueError):
            author.validate_edit(dict(edit,purpose='New task'),[],'bad')
        copied=' '.join('unusualword'+str(i) for i in range(15))
        with self.assertRaises(ValueError):
            author.validate_edit(dict(edit,block=copied),[dict(request=copied)],'bad')

    def test_text_identity_ignores_id_but_not_rule_changes(self):
        base=common.read(common.BASE)
        self.assertEqual(common.text_hash(base),common.text_hash(dict(base,id='alias')))
        self.assertNotEqual(common.text_hash(base),common.text_hash(dict(base,block='changed')))
        with self.assertRaises(ValueError):common.validate_policy(dict(base,purpose='new scope'))

    def test_selection_rule_uses_accuracy_then_length_then_id(self):
        records=[dict(id='a',accuracy=.8,words=10),dict(id='b',accuracy=.9,words=30),
                 dict(id='c',accuracy=.9,words=20),dict(id='d',accuracy=.9,words=20)]
        self.assertEqual(min(records,key=study.rank)['id'],'c')

    def test_freeze_rejects_changed_policy_source_and_population(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); data=p/'test.jsonl';data.write_text('example')
            f=dict(status='frozen',sources=common.sources(),registry_sha256=common.digest(common.REGISTRY),
                   policy_hashes=[common.digest(common.BASE)],recipient_choice={'qwen-2b':{}},
                   data_hashes={'test':common.digest(data)})
            fp=p/'freeze.json';common.write(fp,f)
            common.validate_freeze(fp,'qwen-2b',common.BASE,data,'test')
            data.write_text('changed')
            with self.assertRaises(ValueError):common.validate_freeze(fp,'qwen-2b',common.BASE,data,'test')
            with self.assertRaises(ValueError):common.validate_freeze(None,'qwen-2b',common.BASE,data,'test')
            with patch.object(common,'sources',return_value={}):
                with self.assertRaises(ValueError):common.validate_freeze(fp,'qwen-2b',common.BASE,data,'test')

    def test_http_runner_preserves_wrapper_and_failure_denominator(self):
        for slug,adapter in [('qwen-2b','qwen'),('shieldstral','shieldstral')]:
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);data=p/'data';data.write_text('fixture')
                sent=[]
                def post(base,path,payload):
                    if path=='/tokenize':return {'tokens':[len(payload['prompt'])+ord(payload['prompt'][-1])]}
                    self.assertEqual(path,'/v1/chat/completions');sent.append(payload)
                    raise TimeoutError('private response must not leak')
                with patch.object(run,'check_data',return_value=[self.case()]), patch.object(specialist,'post',side_effect=post):
                    result=run.run(slug,common.BASE,data,'fit',p/'run')
                self.assertEqual(result['n'],1); self.assertEqual(result['errors'],1); self.assertEqual(result['accuracy'],0)
                row=json.loads((p/'run/predictions.jsonl').read_text())
                self.assertNotIn('prompt',row);self.assertNotIn('reason',row)
                self.assertEqual(row['error_type'],'TimeoutError')
                model=common.read(common.REGISTRY)['models'][slug]['model'];policy=common.read(common.BASE)
                expected=(qwen.payload(model,policy,self.case()['prompt'],sent[0]['logprob_token_ids'])
                          if adapter=='qwen' else specialist.payload(adapter,model,policy,self.case()['prompt']))
                expected['logprob_token_ids']=sent[0]['logprob_token_ids']
                self.assertEqual(sent[0],expected)

    def test_alignment_rejects_changed_labels_and_groups(self):
        a=self.case()
        study.align([a],[a])
        with self.assertRaises(ValueError):study.align([a],[dict(a,group='other')])
        with self.assertRaises(ValueError):study.align([a],[dict(a,expected='ALLOW')])


if __name__=='__main__':unittest.main()
