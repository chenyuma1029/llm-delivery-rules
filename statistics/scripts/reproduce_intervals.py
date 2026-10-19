from pathlib import Path
import argparse,csv,json
import numpy as np
from selection_engine import effects,weights_for,conditional_intervals
p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=list(csv.DictReader((a.data_root/'folds.csv').open()));ds=[r['dataset'] for r in rows];w,_=weights_for(ds)
with np.load(a.selection,allow_pickle=False) as z:result={k:z[k] for k in z.files}
ci=conditional_intervals(effects(result,w),ds)
if a.out.exists():raise FileExistsError(a.out)
a.out.write_text(json.dumps(ci,indent=2)+'\n');print('Computed all 11 fixed-OOF conditional intervals.')
