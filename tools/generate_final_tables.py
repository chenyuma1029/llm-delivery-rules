from pathlib import Path
import argparse,json,csv
p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,default=Path('.'));p.add_argument('--out',type=Path,required=True);args=p.parse_args();N=args.source_root/'analysis_summary'
rows={v['key']:v for v in json.loads((N/'summary.json').read_text())}; splits=json.loads((N/'split_sensitivity/summary.json').read_text())
def table(cols,head,lines):return '\\begin{tabular}{'+cols+'}\\toprule\n'+head+'\\\\\\midrule\n'+'\n'.join(x+'\\\\' for x in lines)+'\n\\bottomrule\\end{tabular}\n'
def f(x):return f'{float(x):.3f}'
def ci(v):return '$['+f(v['ci95_lower_pp'])+','+f(v['ci95_upper_pp'])+']$'
labels={'nine':'All nine','exact4':'Exactly four calls (6)','at_most4':'At most four calls (8)','no_judge':'No judge (4)'}
lines=[]
for k in ['nine','exact4','at_most4']:
 for d,arrow in [('S_to_P','$S\\to P$'),('P_to_S','$P\\to S$')]:
  v=rows[k+'_'+d];lines.append(f"{labels[k]} & {arrow} & {f(v['estimate_pp'])} & {ci(v)}")
files={'final_heldout.tex':table('llrr','Candidate set & Transfer & Difference (pp) & Conditional 95\\% interval',lines)}
lines=[]
for t in [90,95,99]:
 v=rows[f'filter_{t}_residual_P_to_S'];lines.append(f"{t}\\% & {f(v['source_accuracy_pp'])} & {f(v['estimate_pp'])} & {ci(v)} & {v['fallback_decisions']}/780")
files['final_filters.tex']=table('rrrrr','Threshold & Accuracy (\\%) & Residual (pp) & Conditional 95\\% interval & Fallbacks',lines)
lines=[]
for v in splits:
 k=v['key']; label=('Filter '+k.split('_')[1]+'\\%') if k.startswith('filter') else labels[k.rsplit('_',3)[0]] if False else ''
 if not label:
  base=k.removesuffix('_S_to_P').removesuffix('_P_to_S');label=labels[base]+(' $S\\to P$' if k.endswith('_S_to_P') else ' $P\\to S$')
 lines.append(f"{label} & {f(v['mean_across_splits_pp'])} & {f(v['median_across_splits_pp'])} & {f(v['minimum_pp'])} & {f(v['maximum_pp'])} & {v['negative_splits']}/{v['zero_splits']}/{v['positive_splits']}")
files['final_splits.tex']=table('lrrrrr','Contrast & Mean & Median & Min. & Max. & $-/0/+$',lines)
grid=list(csv.DictReader((N/'grid_sensitivity.csv').open())); lines=[]
for v in grid:
 st=v['stratum']
 if st.startswith('serializer') or st.startswith('header'):continue
 if st.startswith('ledger_cap:'):
  _,led,cap=st.split(':');label={'collaboration_payload':'Collaboration','end_to_end_multicast':'Multicast','end_to_end_unicast':'Unicast'}[led]+' '+cap
 elif st.startswith('ledger:'):label={'collaboration_payload':'Collaboration (all)','end_to_end_multicast':'Multicast (all)','end_to_end_unicast':'Unicast (all)'}[st.split(':')[1]]
 else:label={'all156':'Full grid','raw_H0':'Raw, zero headers','uniform_ledger':'Equal ledger weights'}.get(st,st.replace('_',' '))
 lines.append(f"{label} & {v['contexts']} & {v['same_data_best_set_changes']} & {f(v['nine_S_to_P_pp'])} & {f(v['nine_P_to_S_pp'])} & {f(v['at_most4_P_to_S_pp'])} & {f(v['filter_95_residual_P_to_S_pp'])}")
files['final_strata.tex']=table('lrrrrrr','Stratum / cap (bytes) & $n$ & Changes & Nine $S\\to P$ & Nine $P\\to S$ & $\\leq4$ $P\\to S$ & Filter 95\\%',lines)
lines=[]
for k,v in rows.items():
 if not (k.startswith('at_most') or k.startswith('filter')):continue
 label=('Filter '+k.split('_')[1]+'\\%') if k.startswith('filter') else ('At most four '+('$S\\to P$' if k.endswith('_S_to_P') else '$P\\to S$'))
 lines.append(f"{label} & {v['negative']} & {v['zero']} & {v['positive']} & {f(v['median_context_pp'])}")
files['final_signs.tex']=table('lrrrr','Contrast & Negative & Zero & Positive & Median (pp)',lines)
seedrows=list(csv.DictReader((N/'split_sensitivity/all_seed_summaries.csv').open()));lines=[]
keys=['nine_S_to_P','nine_P_to_S','exact4_S_to_P','exact4_P_to_S','at_most4_S_to_P','at_most4_P_to_S','filter_90_residual_P_to_S','filter_95_residual_P_to_S','filter_99_residual_P_to_S']
for seed in sorted({v['seed'] for v in seedrows}):
 by={v['key']:v for v in seedrows if v['seed']==seed};lines.append(seed+' & '+' & '.join(f(by[k]['estimate_pp']) for k in keys))
files['final_all_seeds.tex']=table('lrrrrrrrrr','Seed & 9 S/P & 9 P/S & 4 S/P & 4 P/S & $\\leq4$ S/P & $\\leq4$ P/S & F90 & F95 & F99',lines)
args.out.mkdir(parents=True,exist_ok=False)
for name,text in files.items():(args.out/name).write_text(text)
print('Generated',len(files),'tables.')
