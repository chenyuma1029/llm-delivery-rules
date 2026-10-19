"""Aggregate audit for the frozen nine-configuration study. No replay or scoring."""
from pathlib import Path
from fractions import Fraction as F
import argparse,csv,json,hashlib,math
METHODS={'direct1':1,'ao_sc2':2,'ao_sc4':4,'ao_sc8':8,'cl_cand':4,'cl_rat':4,'cl_prefix_832':4,'cl_prefix_1200':4,'cl_prefix_2300':4}
RULES={'strict_abort','partial_commit','direct1_fallback'}
LEDGERS={'collaboration_payload','end_to_end_multicast','end_to_end_unicast'}
SERIALIZERS={'raw_utf8','zlib9_per_packet','gzip9_per_packet_mtime0'}
KEYS=['ledger','budget_bytes','compression','header_bytes']
def require(ok,message):
 if not ok:raise ValueError(message)
def numeric(s,lo=0,hi=None):
 x=float(s);require(math.isfinite(x) and x>=lo and (hi is None or x<=hi),'invalid numeric value');return x
def context(r):
 c=(r['ledger'],int(r['budget_bytes']),r['compression'],int(r['header_bytes']))
 require(c[0] in LEDGERS and c[1]>=0 and c[2] in SERIALIZERS and c[3]>=0,'unknown context');return c
def top(z):return sorted(m for m in z if z[m]==max(z.values()))
def pareto(scores,cost):
 return sorted(m for m in scores if not any(scores[n]>=scores[m] and all(x<=y for x,y in zip(cost[n],cost[m])) and (scores[n]>scores[m] or cost[n]!=cost[m]) for n in scores if n!=m))
def audit(contract,rows,costrows):
 require(contract.get('schema_version')=='1.0','unsupported schema')
 require(contract.get('analysis_level')=='post_freeze_exploratory','wrong analysis level')
 require(contract.get('task_population')=={'fresh_hard_math_v2':300,'mmlu_pro_fresh_v2':400},'declared task denominator mismatch')
 require(contract.get('dataset_weights')=={'fresh_hard_math_v2':0.5,'mmlu_pro_fresh_v2':0.5},'equal dataset weighting required')
 require(contract.get('group_reduction')=='mean A/B within task; AO-SC8 uses one AB','group dependence missing')
 require(contract.get('unit')=='logical_application_bytes','unit not supported')
 require(contract.get('resource_vector')==['requested_solver_calls','frozen_judge_input_plus_output_tokens'],'resource vector not supported')
 for k in ['serializer','topology','packet_order','atomicity','reserve','nonfit','delivery','denominator','uncertainty','provenance']:
  require(isinstance(contract.get(k),str) and bool(contract[k].strip()),'missing contract field '+k)
 declared=[tuple(c) for c in contract['contexts']];require(len(declared)==len(set(declared)) and bool(declared),'duplicate/empty declared contexts')
 grid={}; costs={}; traffic={}
 for r in rows:
  c=context(r);s=r['semantics'];m=r['method'];require(s in RULES and m in METHODS,'unknown method/rule')
  slot=grid.setdefault(c,{}).setdefault(s,{});require(m not in slot,'duplicate score')
  x=F(r['exact_fraction']);require(0<=x<=1,'invalid exact accuracy');require(abs(float(x)-numeric(r['accuracy'],hi=1))<1e-12,'exact/decimal mismatch')
  require(abs(float(x)-.5*(numeric(r['math_accuracy'],hi=1)+numeric(r['mmlu_accuracy'],hi=1)))<1e-12,'macro weighting mismatch');slot[m]=x
 require(set(grid)==set(declared),'declared context coverage mismatch')
 require(all(set(x)==RULES and all(set(z)==set(METHODS) for z in x.values()) for x in grid.values()),'all nine methods and three rules required')
 for r in costrows:
  c=context(r);s=r['semantics'];m=r['method'];k=(c,s,m);require(k not in costs,'duplicate resource record');require(s in RULES and m in METHODS,'unknown cost method/rule')
  calls=numeric(r['requested_solver_calls']);require(calls==METHODS[m],'requested solver calls mismatch')
  ji=numeric(r['judge_input_tokens']);jo=numeric(r['judge_output_tokens']);jt=numeric(r['expected_judge_tokens']);require(abs(ji+jo-jt)<1e-8,'judge token total mismatch')
  require(m.startswith('cl_') or jt==0,'no-judge method has judge charge')
  require(abs(float(grid[c][s][m])-numeric(r['accuracy'],hi=1))<1e-12,'cost/score mismatch')
  admitted=numeric(r['admitted_mean_bytes']);require(admitted<=c[1]+1e-9,'admitted bytes exceed cap')
  numeric(r['noncompletion_macro'],hi=1);costs[k]=(calls,F(str(jt)));traffic[k]=admitted
 require(set(grid)==set(declared),'declared context coverage mismatch')
 expected={(c,s,m) for c in declared for s in RULES for m in METHODS};require(set(costs)==expected,'resource coverage incomplete')
 out=[]
 for c in sorted(grid):
  require(set(grid[c])==RULES and all(set(z)==set(METHODS) for z in grid[c].values()),'all nine methods and three rules required')
  for m in METHODS:require(len({costs[c,s,m] for s in RULES})==1,'frozen costs must not vary by rule')
  for setname,mm in [('nine_configurations',set(METHODS)),('fixed_four_solver_calls',{m for m in METHODS if METHODS[m]==4})]:
   for s in sorted(RULES):
    z={m:grid[c][s][m] for m in mm};v={m:costs[c,s,m] for m in mm}
    other='partial_commit' if s=='strict_abort' else 'strict_abort';tz={m:grid[c][other][m] for m in mm};los=[100*(max(tz.values())-tz[m]) for m in top(z)]
    out.append(dict(zip(KEYS,c),method_set=setname,semantics=s,accuracy_best_set='|'.join(top(z)),accuracy_best_exact=str(max(z.values())),pareto_set='|'.join(pareto(z,v)),same_path_target_rule=other if s!='direct1_fallback' else '',same_path_loss_best_pp=float(min(los)) if s!='direct1_fallback' else '',same_path_loss_worst_pp=float(max(los)) if s!='direct1_fallback' else '',equal_total_compute=False,analysis_level='post_freeze_exploratory'))
 summary={'contexts':len(grid),'nine_same_path_best_set_changes':sum(top(x['strict_abort'])!=top(x['partial_commit']) for x in grid.values()),'all3_changes':sum(len({tuple(top(z)) for z in x.values()})>1 for x in grid.values()),'audit_scope':'declared aggregate coverage, macro arithmetic and resource comparisons; not unique-task coverage, raw replay or gold scoring','task_population_scope':'declared counts only; task membership is not verified by aggregate inputs','heldout_executed':False,'resource_caveat':'Frozen judge tokens are not actual finite-cap executed tokens; no latency/dollar/energy claim.'}
 return out,summary

def main():
 a=argparse.ArgumentParser();a.add_argument('--contract',type=Path,required=True);a.add_argument('--scores',type=Path,required=True);a.add_argument('--resources',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a=a.parse_args()
 rows,summary=audit(json.loads(a.contract.read_text()),list(csv.DictReader(a.scores.read_text().splitlines())),list(csv.DictReader(a.resources.read_text().splitlines())))
 a.out.mkdir(parents=True,exist_ok=False)
 with (a.out/'comparison_records.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary['inputs']={k:{'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in [('contract',a.contract),('scores',a.scores),('resources',a.resources)]}
 (a.out/'report.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
