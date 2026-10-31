import unittest
import numpy as np
import torch
from evals.liquid_finetune.runner import mean_pool,Classifier,optimizer_for
from evals.liquid_finetune.study import select,paired_intervals,score


class LiquidTests(unittest.TestCase):
    def test_pool_excludes_padding_with_gradients(self):
        x=torch.tensor([[[1.,3.],[3.,7.],[100.,100.]]],requires_grad=True)
        p=mean_pool(x,torch.tensor([[1,1,0]]));self.assertTrue(torch.equal(p,torch.tensor([[2.,5.]])))
        p.sum().backward();self.assertTrue(torch.equal(x.grad[0,2],torch.zeros(2)))

    def test_selection_uses_all_seeds(self):
        y=np.array([0,0,1,1])
        candidates={'one_lucky_seed':{'scores':[[.1,.1,.9,.9],[.9,.9,.1,.1],[.9,.9,.1,.1]]},
                    'consistent':{'scores':[[.1,.6,.8,.9]]*3}}
        choices,_=select(y,candidates)
        self.assertEqual(choices['accuracy']['candidate'],'consistent')
        self.assertEqual(len(choices['accuracy']['seed_validation']),3)

    def test_class_errors_and_coverage(self):
        m=score(np.array([0,0,0,1,1]),np.array([.9,.1,.2,.8,.4]),.5)
        self.assertEqual(m['false_blocks'],1);self.assertEqual(m['missed_violations'],1)
        self.assertEqual(m['accuracy'],.6);self.assertEqual(m['coverage'],1)
        with self.assertRaises(ValueError):score(np.array([0,1]),np.array([.1,np.nan]),.5)

    def test_identical_paired_predictions_have_zero_interval(self):
        meta=[dict(group=str(i),expected='BLOCK' if i%2 else 'ALLOW') for i in range(30)]
        p=np.arange(30)%2
        ci=paired_intervals(meta,p,p,repetitions=50)
        self.assertEqual(ci['accuracy'],[0.,0.]);self.assertEqual(ci['balanced_accuracy'],[0.,0.])

    def test_optimizer_updates_backbone_and_head(self):
        from types import SimpleNamespace
        class Body(torch.nn.Module):
            def __init__(self):
                super().__init__();self.config=SimpleNamespace(hidden_size=4);self.embed=torch.nn.Embedding(8,4)
            def forward(self,input_ids,**kw):return SimpleNamespace(last_hidden_state=self.embed(input_ids))
        m=Classifier(Body());opt=optimizer_for(m,.01)
        old=[p.clone().detach() for p in m.parameters()]
        z=m(torch.tensor([[1,2],[3,4]]),torch.ones(2,2))
        torch.nn.functional.binary_cross_entropy_with_logits(z,torch.tensor([0.,1.])).backward();opt.step()
        self.assertTrue(all(not torch.equal(a,b) for a,b in zip(old,m.parameters())))


if __name__=='__main__':unittest.main()
