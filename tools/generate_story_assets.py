#!/usr/bin/env python3
"""Render existing aggregates and contract mechanics; no labels, inference, or CI fitting."""
from pathlib import Path
import argparse,csv,json,hashlib,statistics
from fractions import Fraction
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output-root',type=Path);a=p.parse_args();root=a.source_root;dest=a.output_root or root
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
def rows(n):return list(csv.DictReader((root/n).open()))
scores=rows('audit_report/inputs/scores.csv');resources=rows('audit_report/inputs/resources.csv');held=rows('heldout_summary/heldout_context_summary.csv');boot=rows('heldout_summary/paired_bootstrap.csv');controls=rows('heldout_summary/heldout_by_ledger_cap.csv')
ms=['direct1','ao_sc2','ao_sc4','ao_sc8','cl_cand','cl_rat','cl_prefix_832','cl_prefix_1200','cl_prefix_2300'];labels=['Direct-1','AO-SC2','AO-SC4','AO-SC8','CL-CAND','CL-RAT','CL-PREFIX832','CL-PREFIX1200','CL-PREFIX2300'];label=dict(zip(ms,labels));rules=['strict_abort','partial_commit']
ctxkeys=['ledger','budget_bytes','compression','header_bytes']
def context(r):return tuple(r[k] for k in ctxkeys)
contexts=sorted({context(r) for r in scores});assert len(contexts)==156
lookup={(context(r),r['semantics'],r['method']):Fraction(r['exact_fraction']) for r in scores}
switches=0
for c in contexts:
 tops=[]
 for rule in rules:
  vals={m:lookup[c,rule,m] for m in ms};best=max(vals.values());tops.append({m for m,v in vals.items() if v==best})
 switches+=tops[0]!=tops[1]
assert switches==49
anchor=('end_to_end_multicast','1200','raw_utf8','0')
# Ledger keys remain exactly as declared by source records.
if anchor not in contexts:anchor=next(c for c in contexts if 'multicast' in c[0] and c[1:] == ('1200','raw_utf8','0'))
rs={(r['method'],r['semantics']):r for r in resources if context(r)==anchor}
bests={rule:max(lookup[anchor,rule,m] for m in ms) for rule in rules}
lines=[r'\begin{tabular}{lrrrr}\toprule',r'Configuration & Solver calls & Judge tokens & Strict (\%) & Partial (\%)\\\midrule']
for m in ms:
 rr=rs[m,'strict_abort'];vals=[]
 for rule in rules:
  v=lookup[anchor,rule,m];s=f'{100*float(v):.2f}';vals.append(r'\textbf{'+s+'}' if v==bests[rule] else s)
 lines.append(f"{label[m]} & {float(rr['requested_solver_calls']):.0f} & {float(rr['expected_judge_tokens']):.1f} & {vals[0]} & {vals[1]} \\\\")
lines.append(r'\bottomrule\end{tabular}');anchor_table='\n'.join(lines)+'\n'
sets=[('nine_configurations','Nine configurations'),('fixed_four_solver_calls','Four solver calls')]
lines=[r'\begin{tabular}{lcrr}\toprule',r'Candidate set & Source $\to$ target & Difference (pp) & Conditional 95\% interval\\\midrule']
heldfacts=[]
for mset,name in sets:
 for source,target in [('strict_abort','partial_commit'),('partial_commit','strict_abort')]:
  r=next(r for r in boot if (r['ledger'],r['budget_bytes'],r['method_set'],r['source_rule'],r['target_rule'],r['comparison'])==('ALL','ALL',mset,source,target,'target_minus_source'))
  direction=r'$S\to P$' if source=='strict_abort' else r'$P\to S$'
  v,lo,hi=[float(r[k]) for k in ['estimate_pp','ci95_lower_pp','ci95_upper_pp']]
  lines.append(f'{name} & {direction} & {v:.3f} & [{lo:.3f}, {hi:.3f}] \\\\')
  heldfacts.append({'method_set':mset,'source':source,'target':target,'estimate':v,'ci':[lo,hi]})
lines.append(r'\bottomrule\end{tabular}');held_table='\n'.join(lines)+'\n'
lines=[r'\begin{tabular}{lcrrrrrrrr}\toprule',r'Set & Direction & Source & Target & D1 & AO4 & AO8 & CL-C & Min. & Test-best\\\midrule']
for mset,name in sets+[('no_judge','No judge'),('train_pareto_nine','Train Pareto')]:
 for source,target in [('strict_abort','partial_commit'),('partial_commit','strict_abort')]:
  r=next(r for r in controls if (r['ledger'],r['budget_bytes'],r['method_set'],r['source_rule'],r['target_rule'])==('ALL','ALL',mset,source,target));direction=r'$S\to P$' if source=='strict_abort' else r'$P\to S$';cols=['selected_source_accuracy_pp','selected_target_accuracy_pp','fixed_direct1_accuracy_pp','fixed_ao_sc4_accuracy_pp','fixed_ao_sc8_accuracy_pp','fixed_cl_cand_accuracy_pp','minimum_resource_accuracy_pp','test_oracle_unattainable_accuracy_pp'];vals=' & '.join(f'{float(r[k]):.2f}' for k in cols);lines.append(f'{name} & {direction} & {vals} \\\\')
lines.append(r'\bottomrule\end{tabular}');controls_table='\n'.join(lines)+'\n'
facts={'same_data_changed':switches,'same_data_stable':156-switches,'anchor':anchor,'heldout':heldfacts,'sign_counts':{},'scope':'Existing frozen summaries; no new scoring or bootstrap fitting.'}
for direction,source,target in [('S to P','strict_abort','partial_commit'),('P to S','partial_commit','strict_abort')]:
 nums=[float(r['signed_target_minus_source_pp']) for r in held if (r['method_set'],r['source_rule'],r['target_rule'])==('nine_configurations',source,target)]
 facts['sign_counts'][direction]=[sum(x< -1e-9 for x in nums),sum(abs(x)<=1e-9 for x in nums),sum(x>1e-9 for x in nums)];assert len(nums)==156;assert statistics.median(nums)==0
assert facts['sign_counts']=={'S to P':[8,102,46],'P to S':[3,102,51]}
for sub in ['manuscript_source','supplement_source']:
 out=dest/sub/'generated/tables';out.mkdir(parents=True,exist_ok=True)
 for n,content in [('story_anchor.tex',anchor_table),('story_heldout.tex',held_table),('story_controls.tex',controls_table)]:(out/n).write_text(content)
figdir=dest/'figures';figdir.mkdir(parents=True,exist_ok=True)
blue='#266779';grey='#d9dfe2';orange='#bf6e36';ink='#253238'
fig,axs=plt.subplots(1,2,figsize=(7.3,2.7),gridspec_kw={'width_ratios':[1,1.36]});fig.subplots_adjust(left=.10,right=.96,bottom=.30,top=.73,wspace=.42)
ax=axs[0];ax.set_title('A  Same-data best sets',loc='left',pad=16,fontsize=10.5,weight='bold');ax.barh([.25],[107],height=.40,color=grey,edgecolor=ink,linewidth=.5,hatch='//');ax.barh([.25],[49],left=[107],height=.40,color=blue,edgecolor=ink,linewidth=.5);ax.text(53.5,.25,'107\nunchanged',ha='center',va='center',fontsize=9);ax.text(131.5,.25,'49\nchanged',ha='center',va='center',color='white',fontsize=9);ax.set_xlim(0,166);ax.set_ylim(-.3,.9);ax.set_yticks([]);ax.set_xticks([0,52,104,156]);ax.set_xlabel('Contexts');ax.spines['left'].set_visible(False)
ax=axs[1];ax.set_title('B  Held-out difference signs',loc='left',pad=16,fontsize=10.5,weight='bold')
for y,(d,cts) in enumerate(facts['sign_counts'].items()):
 left=0
 for j,(v,color) in enumerate(zip(cts,[orange,grey,blue])):
  ax.barh(1-y,v,left=left,color=color,edgecolor=ink,linewidth=.5,height=.48,hatch='//' if j==1 else None)
  if v>=6:ax.text(left+v/2,1-y,str(v),ha='center',va='center',color='white' if j==2 else ink,fontsize=9)
  else:ax.annotate(str(v),(left+v/2,1-y+.23),xytext=(left+12,1-y+.56),ha='center',va='center',fontsize=9,arrowprops={'arrowstyle':'-','lw':.6,'color':ink})
  left+=v
ax.set_yticks([1,0],['S to P','P to S']);ax.set_xlim(0,166);ax.set_ylim(-.5,1.7);ax.set_xticks([0,52,104,156]);ax.set_xlabel('Contexts');ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=7)
from matplotlib.patches import Patch
fig.legend([Patch(facecolor=orange,edgecolor=ink),Patch(facecolor=grey,edgecolor=ink,hatch='//'),Patch(facecolor=blue,edgecolor=ink)],['Negative','Zero','Positive'],loc='lower right',bbox_to_anchor=(.99,.015),ncol=3,frameon=False,fontsize=8.5,handlelength=1.4,columnspacing=1.1)
fig.savefig(figdir/'story_choices.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
fig,ax=plt.subplots(figsize=(7.3,2.25));fig.subplots_adjust(left=.015,right=.99,bottom=.06,top=.94);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
boxes=[(.015,.26,.270,.64),(.35,.26,.29,.64),(.715,.26,.27,.64)]
for x,y,w,h in boxes:ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.025',edgecolor=ink,facecolor='#f5f7f7',linewidth=.8))
ax.text(.142,.80,'1  Frozen outputs',ha='center',weight='bold',fontsize=10);ax.text(.142,.53,'Query and ordered answers\nEvidence and judge choice\nNo responses regenerated',ha='center',va='center',fontsize=9,linespacing=1.65)
ax.text(.495,.80,'2  Shared admission',ha='center',weight='bold',fontsize=10);ax.text(.495,.54,'Next answer fits if\n$C + c_i + r_i \\leq B$\nReserve is capacity, not traffic',ha='center',va='center',fontsize=9,linespacing=1.6)
ax.text(.853,.80,'3  Terminal delivery',ha='center',weight='bold',fontsize=10);ax.text(.853,.62,'Complete: final answer',ha='center',fontsize=9);ax.text(.853,.47,'Incomplete strict: empty',ha='center',fontsize=9,color=orange);ax.text(.853,.32,'Incomplete partial: prefix*',ha='center',fontsize=9,color=blue)
for x1,x2 in [(.287,.335),(.653,.70)]:ax.annotate('',xy=(x2,.57),xytext=(x1,.57),arrowprops={'arrowstyle':'->','lw':1,'color':ink})
ax.text(.5,.11,'* Commit the prefix resolution only if its output fits; otherwise return empty.',ha='center',fontsize=8.5)
fig.savefig(figdir/'delivery_contract_story.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
for sub in ['manuscript_source','supplement_source']:
 out=dest/sub/'figures_revision';out.mkdir(parents=True,exist_ok=True)
 for n in ['story_choices.pdf','delivery_contract_story.pdf']:(out/n).write_bytes((figdir/n).read_bytes())
facts['input_sha256']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['audit_report/inputs/scores.csv','audit_report/inputs/resources.csv','heldout_summary/heldout_context_summary.csv','heldout_summary/paired_bootstrap.csv','heldout_summary/heldout_by_ledger_cap.csv']}
(dest/'STORY_ASSET_PROVENANCE.json').write_text(json.dumps(facts,indent=2)+'\n');print(json.dumps(facts,indent=2))
