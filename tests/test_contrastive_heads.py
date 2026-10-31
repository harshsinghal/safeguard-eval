import tempfile
import unittest
from pathlib import Path
import numpy as np
import torch
from evals.contrastive_heads.learn import supervised_contrastive,standardize,Head,neural_predict
from evals.contrastive_heads.study import selections
from evals.contrastive_heads.common import load,write,write_rows,digest

class ContrastiveHeadsTest(unittest.TestCase):
    def test_contrastive_matches_independent_formula(self):
        h=np.array([[1.,2.],[2.,1.],[-1.,-2.],[-2.,-1.]],dtype=np.float64)
        y=np.array([0,0,1,1]);w=np.array([1.,2.,1.,2.]);z=h/np.linalg.norm(h,axis=1,keepdims=True)
        sims=z@z.T/.1;loss=[]
        for i in range(4):
            others=np.arange(4)!=i;positives=others&(y==y[i]);den=np.log(np.exp(sims[i,others]).sum())
            loss.append(-np.mean(sims[i,positives]-den))
        ht=torch.tensor(h,requires_grad=True)
        got=supervised_contrastive(ht,torch.tensor(y),torch.tensor(w));got.backward()
        self.assertAlmostEqual(float(got.detach()),np.average(loss,weights=w),places=10)
        self.assertTrue(torch.isfinite(ht.grad).all())
    def test_no_positive_peers_and_permutation(self):
        h=torch.tensor([[1.,2.],[3.,4.]],requires_grad=True)
        got=supervised_contrastive(h,torch.tensor([0.,1.]),torch.ones(2));got.backward()
        self.assertEqual(float(got.detach()),0);self.assertTrue(torch.isfinite(h.grad).all())
        torch.manual_seed(3);h=torch.randn(6,4);y=torch.tensor([0,0,0,1,1,1]);w=torch.ones(6)
        perm=torch.tensor([2,0,5,1,3,4])
        self.assertAlmostEqual(float(supervised_contrastive(h,y,w)),float(supervised_contrastive(h[perm],y[perm],w[perm])),places=5)
    def test_scaler_uses_fit_only_and_saved_arithmetic(self):
        x=np.array([[1,2],[3,4]],dtype=np.float32);v=np.array([[100,200]],dtype=np.float32)
        scale,xf,xv=standardize(x,v)
        np.testing.assert_array_equal(scale.mean_,[2,3])
        np.testing.assert_array_equal(xv,((v-scale.mean_)/scale.scale_).astype(np.float32))
    def test_prediction_roundtrip(self):
        torch.manual_seed(12);m=Head(4).eval();x=np.arange(20,dtype=np.float32).reshape(5,4)
        with torch.no_grad(): expected=torch.sigmoid(m(torch.from_numpy(x))[0]).numpy()
        np.testing.assert_allclose(neural_predict(m.state_dict(),x),expected,rtol=0,atol=1e-7)
    def test_selection_uses_all_seeds_not_best_seed(self):
        y=np.array([0,0,1,1])
        candidates={'one_lucky_seed':dict(scores=[[0,0,1,1],[1,1,0,0],[1,1,0,0]]),
                    'consistent':dict(scores=[[0,1,1,1]]*3)}
        chosen,_=selections(y,candidates)
        self.assertEqual(chosen['balanced']['candidate'],'consistent')
        self.assertEqual(len(chosen['balanced']['seed_validation']),3)
    def test_feature_alignment_and_hash_guard(self):
        with tempfile.TemporaryDirectory() as td:
            state=Path(td);meta=[dict(id='a',expected='ALLOW',prompt_sha256='x',group='g')]
            mp=state/'metadata/wildguard/fit.jsonl.gz';write_rows(mp,meta)
            folder=state/'features/wildguard/modernbert/fit';folder.mkdir(parents=True)
            np.save(folder/'features.npy',np.zeros((1,768),dtype=np.float32))
            manifest=dict(ids=['a'],metadata_sha256=digest(mp),artifacts={'features.npy':digest(folder/'features.npy')})
            write(folder/'manifest.json',manifest);self.assertEqual(load(state,'wildguard','modernbert','fit')[1].shape,(1,768))
            manifest['ids']=['b'];write(folder/'manifest.json',manifest)
            with self.assertRaises(ValueError):load(state,'wildguard','modernbert','fit')

if __name__=='__main__':unittest.main()
