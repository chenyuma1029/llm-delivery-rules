from pathlib import Path
import argparse,csv,json
import numpy as np
from selection_engine import evaluate,weights_for,summarize
p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--all-splits',action='store_true');a=p.parse_args()
s=json.loads((a.data_root/'schema.json').read_text());z=np.load(a.data_root/'task_metrics.npz',allow_pickle=False);rows=list(csv.DictReader((a.data_root/'folds.csv').open()));w,_=weights_for([r['dataset'] for r in rows]);a.out.mkdir(parents=True,exist_ok=False)
columns=[c for c in rows[0] if c.startswith('seed_')] if a.all_splits else ['original_fold'];summary=[]
for col in columns:
 fold=np.array([int(r[col]) for r in rows],dtype=np.int8)
 rr=evaluate(z['correctness_times_two'],z['full_fit_times_two'],z['delivered_available_times_two'],z['frozen_resources_times_two'],s['methods'],s['rules'],fold,w)
 for v in summarize(rr,w):summary.append({'fold_column':col,**v})
 if not a.all_splits:np.savez_compressed(a.out/'oof_results.npz',**rr,folds=fold)
 print(col,'computed',flush=True)
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
