"""Independent exact-count selection on supplied task-level derived metrics.

No expected-result inputs, reference answers, model calls or network access.
All selectors use training tasks only; test-oracle values are separate controls.
"""
import hashlib
import numpy as np

SETS = {
    'nine': None,
    'exact4': ['ao_sc4','cl_cand','cl_rat','cl_prefix_832','cl_prefix_1200','cl_prefix_2300'],
    'at_most4': ['direct1','ao_sc2','ao_sc4','cl_cand','cl_rat','cl_prefix_832','cl_prefix_1200','cl_prefix_2300'],
    'no_judge': ['direct1','ao_sc2','ao_sc4','ao_sc8'],
}
TRANSFERS=[('strict_abort','partial_commit'),('partial_commit','strict_abort'),('strict_abort','strict_abort'),('partial_commit','partial_commit'),('direct1_fallback','direct1_fallback')]
ROLES=['selected_source','selected_target','fixed_cl_cand','fixed_ao_sc4','fixed_direct1','fixed_ao_sc8','minimum_resource','test_oracle_unattainable']
THRESHOLDS=[90,95,99]

def weights_for(datasets):
    names=list(dict.fromkeys(datasets));assert len(names)==2
    ix=[np.flatnonzero(np.asarray(datasets)==n) for n in names]
    assert [len(x) for x in ix]==[300,400]
    w=np.empty(700,dtype=np.int64);w[ix[0]]=4;w[ix[1]]=3
    return w,ix

def make_folds(tasks, seed):
    result=np.full(len(tasks),-1,dtype=np.int8)
    for ds in dict.fromkeys(t[0] for t in tasks):
        pool=[i for i,t in enumerate(tasks) if t[0]==ds]
        ordered=sorted(pool,key=lambda i:(hashlib.sha256(f'{seed}|{tasks[i][0]}|{tasks[i][1]}'.encode()).hexdigest(),tasks[i][1]))
        for rank,i in enumerate(ordered):result[i]=rank%5
    return result

def weighted_counts(values, mask, weights):
    return np.tensordot(values[...,mask].astype(np.int64),weights[mask],axes=([-1],[0]))

def lexical_max(nums, candidates, methods):
    ordered=sorted(candidates,key=lambda i:methods[i])
    return max(ordered,key=lambda i:int(nums[i]))

def completion_choice(partial_counts, completion_counts, denominator, methods, threshold_percent):
    eligible=np.flatnonzero(completion_counts*100 >= threshold_percent*denominator).tolist()
    n=len(eligible);fallback=n==0
    if fallback:eligible=np.flatnonzero(completion_counts==completion_counts.max()).tolist()
    return lexical_max(partial_counts,eligible,methods),fallback,n

def fit_fold(y,fit,resources,methods,rules,train,weights):
    """Return choices for a single fold; no test labels/completion enter."""
    count=weighted_counts(y,train,weights)
    comp=weighted_counts(fit,train,weights)
    cost=weighted_counts(resources.transpose(0,2,1),train,weights)
    denominator=2*weights[train].sum()
    sets={k:list(range(len(methods))) if v is None else [methods.index(m) for m in v] for k,v in SETS.items()}
    choices=np.empty((y.shape[0],len(sets),len(rules)),dtype=np.uint8)
    minimum=[]
    for si,ids in enumerate(sets.values()):
        minimum.append(min(ids,key=lambda i:(int(cost[i,0]),int(cost[i,3]+cost[i,4]),methods[i])))
        for c in range(y.shape[0]):
            for rr in range(len(rules)):choices[c,si,rr]=lexical_max(count[c,rr],ids,methods)
    filtered=np.empty((y.shape[0],3),dtype=np.uint8);fallback=np.zeros_like(filtered,dtype=bool);eligible=np.zeros_like(filtered)
    for c in range(y.shape[0]):
        for ti,tau in enumerate(THRESHOLDS):
            filtered[c,ti],fallback[c,ti],eligible[c,ti]=completion_choice(count[c,rules.index('partial_commit')],comp[c],denominator,methods,tau)
    return choices,np.array(minimum),filtered,fallback,eligible

def evaluate(y,fit,available,resources,methods,rules,folds,weights):
    C,_,M,T=y.shape;S=len(SETS)
    shape=(C,S,len(TRANSFERS),len(ROLES),T)
    outcome=np.zeros(shape,dtype=np.uint8)
    completion=np.zeros(shape,dtype=np.uint8)
    delivery=np.zeros(shape,dtype=np.uint8)
    chosen=np.zeros((C,S,5,8,5),dtype=np.uint8)
    filter_oof=np.zeros((C,3,T),dtype=np.uint8)
    filter_fit=np.zeros_like(filter_oof)
    filter_choice=np.zeros((C,3,5),dtype=np.uint8)
    filter_fallback=np.zeros((C,3,5),dtype=bool);filter_eligible=np.zeros((C,3,5),dtype=np.uint8)
    sets={k:list(range(M)) if v is None else [methods.index(m) for m in v] for k,v in SETS.items()}
    for f in range(5):
        train=folds!=f;test=folds==f;idx=np.flatnonzero(test)
        assert weights[test].sum()==480 and weights[train].sum()==1920
        selection,minimum,filtered,fallback,eligible=fit_fold(y,fit,resources,methods,rules,train,weights)
        test_count=weighted_counts(y,test,weights)
        filter_choice[:,:,f]=filtered;filter_fallback[:,:,f]=fallback;filter_eligible[:,:,f]=eligible
        for c in range(C):
            for ti in range(3):
                m=filtered[c,ti];filter_oof[c,ti,idx]=y[c,rules.index('strict_abort'),m,idx];filter_fit[c,ti,idx]=fit[c,m,idx]
            for si,ids in enumerate(sets.values()):
                for di,(source,target) in enumerate(TRANSFERS):
                    sr=rules.index(source);tr=rules.index(target)
                    rr=[selection[c,si,sr],selection[c,si,tr],methods.index('cl_cand'),methods.index('ao_sc4'),methods.index('direct1'),methods.index('ao_sc8'),minimum[si],lexical_max(test_count[c,tr],ids,methods)]
                    chosen[c,si,di,:,f]=rr
                    for role,m in enumerate(rr):
                        outcome[c,si,di,role,idx]=y[c,tr,m,idx]
                        completion[c,si,di,role,idx]=fit[c,m,idx]
                        delivery[c,si,di,role,idx]=available[c,tr,m,idx]
    return {'correctness_times_two':outcome,'full_fit_times_two':completion,'delivered_available_times_two':delivery,'selected_method_indices_by_fold':chosen,'filter_correctness_times_two':filter_oof,'filter_full_fit_times_two':filter_fit,'filter_method_indices_by_fold':filter_choice,'filter_fallback_by_fold':filter_fallback,'filter_eligible_count_by_fold':filter_eligible}

def accuracy_pp(values,weights):
    return np.tensordot(values.astype(np.float64),weights,axes=([-1],[0]))/4800*100

def effects(result,weights):
    out={};y=result['correctness_times_two'].astype(np.int16)
    for si,name in enumerate(SETS):
        for di,direction in enumerate(['S_to_P','P_to_S']):
            out[name+'_'+direction]=(y[:,si,di,1]-y[:,si,di,0])
    for ti,tau in enumerate(THRESHOLDS):
        out[f'filter_{tau}_residual_P_to_S']=y[:,0,1,1]-result['filter_correctness_times_two'][:,ti].astype(np.int16)
    return out

def summarize(result,weights):
    records=[];y=result['correctness_times_two']
    for key,difference in effects(result,weights).items():
        ctx=accuracy_pp(difference,weights)
        if key.startswith('filter_'):
            ti=THRESHOLDS.index(int(key.split('_')[1]));source=result['filter_correctness_times_two'][:,ti];target=y[:,0,1,1]
            extra={'fallback_decisions':int(result['filter_fallback_by_fold'][:,ti].sum())}
        else:
            name,direction=key.rsplit('_',3)[0],None
            name=key.removesuffix('_S_to_P').removesuffix('_P_to_S');si=list(SETS).index(name);di=0 if key.endswith('S_to_P') else 1
            source=y[:,si,di,0];target=y[:,si,di,1];extra={}
        records.append(dict(key=key,estimate_pp=float(ctx.mean()),median_context_pp=float(np.median(ctx)),min_context_pp=float(ctx.min()),max_context_pp=float(ctx.max()),negative=int((ctx<0).sum()),zero=int((ctx==0).sum()),positive=int((ctx>0).sum()),source_accuracy_pp=float(accuracy_pp(source,weights).mean()),target_accuracy_pp=float(accuracy_pp(target,weights).mean()),**extra))
    return records

def conditional_intervals(differences,datasets,seed=20261008,replicates=10000):
    """All methods/contexts of a sampled task travel together; choices fixed."""
    _,ix=weights_for(datasets);rng=np.random.default_rng(seed)
    counts=[rng.multinomial(len(g),np.full(len(g),1/len(g)),size=replicates).astype(float) for g in ix]
    keys=list(differences);task=np.array([differences[k].astype(float).mean(axis=0)*50 for k in keys])
    samples=sum(counts[j]@task[:,g].T/len(g)*.5 for j,g in enumerate(ix))
    bounds=np.quantile(samples,[.025,.975],axis=0)
    return {k:{'ci95_lower_pp':float(bounds[0,i]),'ci95_upper_pp':float(bounds[1,i]),'replicates':replicates,'seed':seed,'scope':'conditional_on_fixed_oof_choices; no refit; no multiplicity adjustment'} for i,k in enumerate(keys)}
