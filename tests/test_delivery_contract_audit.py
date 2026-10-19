import unittest,csv,json,copy
from pathlib import Path
from fractions import Fraction as F
from delivery_contract_audit import audit,pareto,top
D=Path(__file__).resolve().parents[1]/'audit_report'
class AuditBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((D/'inputs/contract.json').read_text());self.s=list(csv.DictReader((D/'inputs/scores.csv').read_text().splitlines()));self.r=list(csv.DictReader((D/'inputs/resources.csv').read_text().splitlines()))
 def test_frozen_negative_comparison(self):
  out,s=audit(self.c,self.s,self.r);self.assertEqual((s['contexts'],s['nine_same_path_best_set_changes'],s['all3_changes']),(156,49,67))
  x=[r for r in out if r['ledger']=='end_to_end_multicast' and r['budget_bytes']==1200 and r['compression']=='raw_utf8' and r['header_bytes']==0 and r['method_set']=='fixed_four_solver_calls' and r['semantics']!='direct1_fallback'];self.assertEqual([r['accuracy_best_set'] for r in x],['cl_cand','cl_cand'])
 def test_no_method_drop(self):
  with self.assertRaises(ValueError):audit(self.c,self.s[:-1],self.r[:-1])
 def test_no_missing_as_zero(self):
  self.s[0]['exact_fraction']=''
  with self.assertRaises(ValueError):audit(self.c,self.s,self.r)
 def test_full_denominator(self):
  self.c['task_population']['fresh_hard_math_v2']-=1
  with self.assertRaises(ValueError):audit(self.c,self.s,self.r)
 def test_wrong_macro(self):
  self.s[0]['math_accuracy']='0'
  with self.assertRaises(ValueError):audit(self.c,self.s,self.r)
 def test_duplicate(self):
  with self.assertRaises(ValueError):audit(self.c,self.s+self.s[:1],self.r)
 def test_cap_violation(self):
  self.r[0]['admitted_mean_bytes']='999999'
  with self.assertRaises(ValueError):audit(self.c,self.s,self.r)
 def test_same_calls_not_equal_compute(self):
  self.assertEqual(pareto({'a':F(1,2),'b':F(1,2)},{'a':(4,F(0)),'b':(4,F(2))}),['a'])
  self.assertEqual(top({'a':F(1,2),'b':F(1,2)}),['a','b'])
 def test_nonfinite_rejected(self):
  self.r[0]['judge_input_tokens']='nan'
  with self.assertRaises(ValueError):audit(self.c,self.s,self.r)
if __name__=='__main__':unittest.main()
