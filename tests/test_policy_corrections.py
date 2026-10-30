import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from evals.policy_corrections import common,study,author
from evals.policy_corrections.prepare import representatives
from evals.leaderboard.metrics import decisions,metrics
from evals.run import build_payload
from evals.qwen_policy.run import render


class CorrectionTests(unittest.TestCase):
    def test_additions_fit_budget_and_reach_both_native_adapters(self):
        base=common.read(common.ROOT/'published_runs/2026-10-30-shield-probe/policy.json')
        p=copy.deepcopy(base);p['allow']+='\n\n'+author.ALLOW;p['block']+='\n\n'+author.BLOCK
        self.assertLessEqual(len(author.ALLOW.split()),150)
        self.assertLessEqual(len(author.BLOCK.split()),150)
        self.assertLessEqual(len((author.EXAMPLE_ALLOW+' '+author.EXAMPLE_BLOCK).split()),120)
        payload=build_payload('shieldstral',common.MODELS['shieldstral']['model'],p,'safe input')
        for text in [render(p),payload['messages'][1]['content']]:
            self.assertIn(author.ALLOW,text);self.assertIn(author.BLOCK,text)
        for field in ['purpose','block','allow','precedence']:self.assertTrue(p[field].startswith(base[field]))

    def test_representative_selection_does_not_depend_on_source_order(self):
        rows=[dict(id=str(i),group='g'+str(i//3)) for i in range(12)]
        self.assertEqual(representatives(rows,'audit'),representatives(rows[::-1],'audit'))
        self.assertEqual(len(representatives(rows,'audit')),4)

    def test_missing_score_remains_an_error(self):
        c=dict(score=[.9,None,.1,.2],prediction=[1,-1,0,0])
        p=decisions(c,.5);m=metrics([1,1,0,0],p)
        self.assertEqual(m['recall'],.5);self.assertEqual(m['unresolved'],1)

    def build_state(self,root):
        self.meta={};self.old=[]
        for split in ['discovery','validation','holdout','test']:
            meta=[dict(id=f'{split}-{i}',expected='BLOCK' if i%2 else 'ALLOW',
                group=f'{split}-g{i}',prompt_sha256=str(i)+split,subcategory='x',adversarial=bool(i%3),split=split)
                for i in range(48)]
            self.meta[split]=meta
            common.write_rows(root/'metadata'/(split+'.jsonl.gz'),meta)
        hashes={('sealed-inputs' if s in ('holdout','test') else 'inputs')+'/'+s+'.jsonl':'hash-'+s for s in self.meta}
        for pid in common.POLICIES:common.write(root/'policies'/(pid+'.json'),dict(id=pid))
        common.write(root/'data-manifest.json',dict(hashes=hashes))
        for name in ['authoring.json','error-review.json','discovery-summary.json','prior-use-audit.json']:common.write(root/name,{})
        common.write_rows(root/'discovery-errors.jsonl.gz',[])
        study.register(root)

    def output(self,root,model,pid,split,scores):
        m=self.meta[split];manifest=common.read(root/'data-manifest.json')
        inp=('sealed-inputs' if split in ('holdout','test') else 'inputs')+'/'+split+'.jsonl'
        common.write(common.output_path(root,model,pid,split),dict(ids=[r['id'] for r in m],scores=list(scores),
            records=[dict(id=r['id'],score=float(s)) for r,s in zip(m,scores)],model=common.MODELS[model],
            policy_sha256=common.digest(root/'policies'/(pid+'.json')),sources=common.sources(),
            registration_sha256=common.digest(root/'registration.json'),input_sha256=manifest['hashes'][inp],
            metadata_sha256=common.digest(root/'metadata'/(split+'.jsonl.gz')),
            freeze_sha256=common.digest(root/'freeze.json') if split in ('holdout','test') else None))

    def test_full_staged_selection_evaluation_and_mutation_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.build_state(root)
            perfect=[.9 if i%2 else .1 for i in range(48)]
            baseline=perfect.copy();baseline[0]=.95;baseline[1]=.05
            for pid in common.POLICIES:
                vals=perfect if pid=='p2' else baseline
                for split in ['discovery','validation']:self.output(root,'shieldstral',pid,split,vals)
            oldread=study.read
            def read_override(path):
                if str(path).endswith('feature-provenance/shieldstral/fit/records.json'):
                    return [dict(id=r['id'],native_score=s) for r,s in zip(self.meta['discovery'],baseline)]
                return oldread(path)
            with patch.object(study,'read',side_effect=read_override):study.select_shield(root)
            self.assertEqual(common.read(root/'shield-selection.json')['selected_revision'],'p2')
            # Transfer deliberately worsens Qwen; it must still use p2, not a
            # Qwen-specific candidate or any held-out outcomes.
            for pid in ['p0','p2']:self.output(root,'qwen',pid,'validation',perfect if pid=='p0' else baseline)
            study.freeze(root);f=common.read(root/'freeze.json')
            self.assertEqual(f['models']['qwen']['primary']['revised-tuned']['policy'],'p2')
            for model in common.MODELS:
                for pid in ['p0','p2']:
                    for split in ['holdout','test']:
                        self.output(root,model,pid,split,perfect if pid=='p2' else baseline)
            study.evaluate(root);study.verify(root)
            # Outputs cannot be silently reordered; metadata and freeze hashes
            # bind each classification to its original population and selection.
            path=common.output_path(root,'qwen','p2','test');original=common.read(path)
            bad=copy.deepcopy(original);bad['ids']=bad['ids'][::-1];common.write(path,bad)
            with self.assertRaisesRegex(ValueError,'identity/order'):common.load_output(root,'qwen','p2','test')
            common.write(path,original)
            path=root/'policies/p2.json';common.write(path,dict(id='changed'))
            with self.assertRaisesRegex(ValueError,'Registered artifact'):study.check_freeze(root)


if __name__=='__main__':unittest.main()
