import tempfile
import unittest
import contextlib
import io
from pathlib import Path
from unittest import mock
import numpy as np
from evals.shield_probe import common, study
from evals.leaderboard.metrics import select, decisions, metrics


class ShieldProbeTests(unittest.TestCase):
    def test_content_pooling_excludes_policy_specials_and_padding(self):
        offsets=[(0,0),(0,6),(6,9),(9,13),(13,18),(18,21),(0,0)]
        np.testing.assert_array_equal(common.content_mask(offsets,10,18),
                                      [False,False,False,True,True,False,False])

    def test_concatenation_keeps_each_examples_two_spaces_separate(self):
        a=np.array([[1,2],[3,4]]);b=np.array([[10],[20]])
        np.testing.assert_array_equal(common.matrix({'q':a,'p':b},['q','p']),[[1,2,10],[3,4,20]])
        with self.assertRaises(ValueError):common.matrix({'q':a,'p':b[:1]},['q','p'])

    def test_combined_missing_representation_remains_unresolved(self):
        v={'qwen':np.array([True,False]),'shieldstral':np.array([True,True])}
        mask=study.validity_for(v,['qwen-l32-mean','shieldstral-l26-last'])
        c=study.candidate(np.array([.9,np.nan]),mask)
        self.assertEqual(c,dict(score=[.9,None],prediction=[1,-1]))
        self.assertEqual(metrics([1,0],decisions(c,.5))['unresolved'],1)

    def test_scaler_fits_training_only_and_saved_equation_reproduces(self):
        x=np.array([[1.,3.],[2.,5.],[9.,9.],[10.,11.]])
        p,it=study.fit_linear(x,np.array([0,0,1,1]),.1)
        np.testing.assert_allclose(p['mean'],x.mean(0))
        original=p['mean'].copy()
        study.predict(p,np.full((2,2),999.))
        np.testing.assert_array_equal(p['mean'],original)
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/'fit.npz';np.savez_compressed(file,**p)
            with np.load(file,allow_pickle=False) as q:
                np.testing.assert_array_equal(study.predict(p,x),study.predict(q,x))

    def test_duplicate_groups_and_content_cannot_cross_splits(self):
        r=dict(id='a',group='g',prompt_sha256='h')
        for changed in (dict(r,id='b'),dict(r,id='b',group='other')):
            with self.assertRaises(ValueError):common.assert_disjoint([r],[changed])

    def test_metric_optimizes_class_balance_not_raw_accuracy(self):
        y=np.array([0]*9+[1])
        c={'always-allow':dict(prediction=[0]*10,score=None),
           'catches':dict(prediction=[1,1]+[0]*7+[1],score=None)}
        chosen,_=select(y,c)
        self.assertEqual(chosen['balanced']['candidate'],'catches')
        self.assertLess(chosen['balanced']['metrics']['accuracy'],.9)

    def test_feature_order_and_hash_are_strict(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);meta=root/'metadata/fit.jsonl.gz'
            common.write_rows(meta,[dict(id='a')])
            folder=root/'features/qwen/fit';folder.mkdir(parents=True)
            common.write(folder/'manifest.json',dict(ids=['b'],metadata_sha256=common.digest(meta)))
            with self.assertRaisesRegex(ValueError,'order'):common.load_features(root,'qwen','fit')

    def test_freeze_rejects_mutated_fitted_parameters(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);common.write(root/'data-manifest.json',{})
            common.write(root/'fits.json',{'coefficient':1})
            common.write(root/'freeze.json',dict(sources={},
                data_manifest_sha256=common.digest(root/'data-manifest.json'),
                artifacts={'fits.json':common.digest(root/'fits.json')}))
            with mock.patch.object(study,'source_hashes',return_value={}):
                study.check_freeze(root)
                common.write(root/'fits.json',{'coefficient':2})
                with self.assertRaisesRegex(ValueError,'artifact changed'):study.check_freeze(root)

    def test_complete_train_freeze_test_pipeline_with_synthetic_features(self):
        rng=np.random.default_rng(7)
        small={k:{**v,'width':2} for k,v in common.MODELS.items()}
        with tempfile.TemporaryDirectory() as t, mock.patch.dict(common.MODELS,small), \
                mock.patch.object(study,'historical_controls',return_value={}):
            root=Path(t);common.write(root/'data-manifest.json',{})
            common.write(root/'policy.json',{'id':'synthetic-test'})
            for split,n in [('fit',40),('validation',20),('test',20)]:
                y=np.arange(n)%2
                meta=[dict(id=f'{split}-{i}',group=f'{split}-{i}',expected='BLOCK' if yy else 'ALLOW',
                           prompt_sha256=f'{split}-{i}',subcategory='test',adversarial=False)
                      for i,yy in enumerate(y)]
                meta_path=root/'metadata'/(split+'.jsonl.gz');common.write_rows(meta_path,meta)
                for model in common.MODELS:
                    folder=root/'features'/model/split;folder.mkdir(parents=True)
                    for key in common.keys(model):
                        a=rng.normal(size=(n,2));a[:,0]+=y*1.5
                        np.save(folder/(key+'.npy'),a)
                    common.write(folder/'records.json',[dict(id=r['id'],native_score=float(.2+.6*yy)) for r,yy in zip(meta,y)])
                    common.write(folder/'manifest.json',dict(ids=[r['id'] for r in meta],
                        metadata_sha256=common.digest(meta_path),valid=[True]*n,
                        artifacts={p.name:common.digest(p) for p in folder.glob('*.npy')},
                        sources=common.source_hashes(),policy_sha256=common.digest(root/'policy.json'),model=common.MODELS[model]))
            with contextlib.redirect_stdout(io.StringIO()):
                study.train(root)
                frozen=common.digest(root/'freeze.json')
                study.evaluate(root)
                study.reproduce(root)
                from tools.verify_shield_probe import verify
                verify(root)
            self.assertEqual(frozen,common.digest(root/'freeze.json'))
            result=common.read(root/'test-results.json')
            self.assertEqual(result['profiles']['balanced']['primary-combined']['test']['n'],20)
            self.assertEqual(len(result['paired_differences']),26)

    def test_score_combination_uses_both_models_and_preserves_missing(self):
        meta=[{'id':'a'},{'id':'b'}]
        def read_fake(path):
            scores=[.9,.8] if 'qwen' in str(path) else [.1,None]
            return [dict(id=r['id'],native_score=s) for r,s in zip(meta,scores)]
        with mock.patch.object(study,'read',side_effect=read_fake):
            out=study.direct_candidates(Path('/unused'),'fit',meta,
                {'qwen':np.array([True,True]),'shieldstral':np.array([True,False])})
        self.assertAlmostEqual(out['score-equal-probability']['score'][0],.5)
        self.assertAlmostEqual(out['score-equal-logodds']['score'][0],.5)
        self.assertEqual(out['score-equal-logodds']['prediction'][1],-1)
        self.assertIsNone(out['score-equal-probability']['score'][1])

    def test_unequal_native_score_order_is_rejected(self):
        with mock.patch.object(study,'read',return_value=[{'id':'wrong','native_score':.5}]):
            with self.assertRaisesRegex(ValueError,'order'):
                study.direct_candidates(Path('/unused'),'fit',[{'id':'right'}],
                    {'qwen':np.ones(1,dtype=bool),'shieldstral':np.ones(1,dtype=bool)})


if __name__=='__main__':unittest.main()
