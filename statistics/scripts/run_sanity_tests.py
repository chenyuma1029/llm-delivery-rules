import unittest
import numpy as np
from selection_engine import completion_choice,fit_fold,SETS,accuracy_pp,effects

class SelectorChecks(unittest.TestCase):
    def test_threshold_equality(self):
        self.assertEqual(completion_choice(np.array([20,30]),np.array([90,89]),100,['a','b'],90),(0,False,1))
    def test_empty_filter_uses_best_completion_before_accuracy(self):
        self.assertEqual(completion_choice(np.array([100,1]),np.array([10,80]),100,['a','b'],90),(1,True,0))
    def test_completion_tie_then_partial_accuracy(self):
        self.assertEqual(completion_choice(np.array([2,4]),np.array([80,80]),100,['a','b'],90)[0],1)
    def test_accuracy_tie_uses_lexical_identifier(self):
        self.assertEqual(completion_choice(np.array([4,4]),np.array([95,95]),100,['z','a'],90)[0],1)
    def test_candidate_sets(self):
        self.assertEqual(len(SETS['exact4']),6);self.assertEqual(len(SETS['at_most4']),8)
        self.assertLess(set(SETS['exact4']),set(SETS['at_most4']))
    def test_test_labels_and_completion_never_change_training_choice(self):
        rng=np.random.default_rng(8);methods=['direct1','ao_sc2','ao_sc4','ao_sc8','cl_cand','cl_rat','cl_prefix_832','cl_prefix_1200','cl_prefix_2300']
        y=rng.integers(0,3,(2,3,9,700),dtype=np.uint8);f=rng.integers(0,3,(2,9,700),dtype=np.uint8);res=np.ones((9,700,5),dtype=np.int64)
        weights=np.array([4]*300+[3]*400);train=np.arange(700)%5!=0
        before=fit_fold(y,f,res,methods,['strict_abort','partial_commit','direct1_fallback'],train,weights)
        y[...,~train]=2-y[...,~train];f[...,~train]=2-f[...,~train];res[:,~train,:]=1000
        after=fit_fold(y,f,res,methods,['strict_abort','partial_commit','direct1_fallback'],train,weights)
        for a,b in zip(before,after):np.testing.assert_array_equal(a,b)
    def test_group_weights_and_negative_signed_difference(self):
        w=np.array([4]*300+[3]*400);v=np.zeros(700,dtype=np.int16);v[0]=-2;v[300]=1
        self.assertAlmostEqual(float(accuracy_pp(v,w)),(-8+3)/48)
    def test_same_rule_difference_zero_and_no_unsigned_underflow(self):
        a=np.array([0,1,2],dtype=np.uint8)
        np.testing.assert_array_equal(a.astype(np.int16)-a.astype(np.int16),[0,0,0])
        self.assertEqual(int((a.astype(np.int16)-a[::-1].astype(np.int16))[0]),-2)

if __name__=='__main__':unittest.main()
