"""Question-paired inference. Never pool example sets or repeated runs."""
import csv
import json
import math
import random
from collections import Counter, defaultdict
import numpy as np
from .common import ROOT, digest, read_json, write_json
from .data import GSM8K
from .store import Store

UNAVAILABLE = {'infrastructure_error', 'execution_unavailable', 'context_overflow'}
CONTRASTS = [('K3', 'K4'), ('K5', 'K4'), ('K7', 'K6'), ('K8', 'K7')]


def paired_ci(a, b, samples=10000, seed=20261021):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) != len(b) or not len(a): raise ValueError('Nonempty aligned pairs required')
    delta = a-b
    rng = np.random.default_rng(seed)
    boot = []
    for start in range(0, samples, 250):
        indices = rng.integers(0, len(a), size=(min(250, samples-start), len(a)))
        boot.extend(delta[indices].mean(axis=1))
    return float(delta.mean()), [float(x) for x in np.quantile(boot, [0.025, 0.975])]


def mcnemar(a, b):
    plus = int(sum(bool(x) and not bool(y) for x,y in zip(a,b)))
    minus = int(sum(bool(y) and not bool(x) for x,y in zip(a,b)))
    n = plus+minus
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(min(plus,minus)+1)) / (2**n)) if n else 1.0
    return dict(a_only=int(plus), b_only=int(minus), p=float(p))


def holm(pvalues, family_size=None):
    size = family_size or len(pvalues)
    order = sorted(range(len(pvalues)), key=lambda i:pvalues[i])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank,i in enumerate(order):
        running = max(running, min(1.0, (size-rank)*pvalues[i]))
        adjusted[i] = running
    return adjusted


def paired_permutation(delta, samples=10000, seed=20261021):
    d = np.asarray(delta, float)
    observed = abs(float(d.mean()))
    rng = np.random.default_rng(seed)
    exceed = 0
    for start in range(0,samples,250):
        signs = rng.choice([-1,1],size=(min(250,samples-start),len(d)))
        exceed += int((np.abs((signs*d).mean(axis=1)) >= observed-1e-12).sum())
    return (exceed+1)/(samples+1)


def summarize(config, run_id):
    store = Store(ROOT/config['database'])
    meta = store.metadata(run_id)
    records = [r for state,r in store.records(run_id) if state == 'complete']
    identity = meta['identity']
    planned = len(identity['question_ids'])
    cells = defaultdict(list)
    for r in records: cells[(r['model_id'],r['condition_id'])].append(r)
    rows = []
    for model in identity['models']:
        for condition in identity['conditions']:
            rs = cells[(model,condition['id'])]
            evaluable = [r for r in rs if r['status'] not in UNAVAILABLE]
            generated = [r for r in rs if r.get('raw_output') is not None]
            executable = [r for r in evaluable if r.get('executable') is True]
            ncorrect = sum(r.get('correct') is True for r in rs)
            row = dict(model=model, condition=condition['id'], pair=identity['demonstration_pair'],
                       planned=planned, recorded=len(rs), generated=len(generated), evaluable=len(evaluable),
                       unavailable=len(rs)-len(evaluable), missing=planned-len(rs), correct=ncorrect,
                       complete=len(evaluable)==planned, accuracy_lower_bound=ncorrect/planned,
                       accuracy=ncorrect/planned if len(evaluable)==planned else None,
                       accuracy_evaluable=ncorrect/len(evaluable) if evaluable else None,
                       parseable=sum(bool(r.get('parseable')) for r in evaluable),
                       parseability=sum(bool(r.get('parseable')) for r in evaluable)/planned,
                       executable=len(executable), executability=len(executable)/planned if condition['arm'] != 'K2' else None,
                       accuracy_executable_selected=sum(bool(r.get('correct')) for r in executable)/len(executable) if executable else None,
                       input_tokens=sum(r.get('input_tokens') or 0 for r in rs), output_tokens=sum(r.get('output_tokens') or 0 for r in rs),
                       generation_seconds=sum(r.get('generation_wall_seconds') or 0 for r in rs),
                       load_seconds=sum(r.get('load_seconds') or 0 for r in rs),
                       prompt_seconds=sum(r.get('prompt_seconds') or 0 for r in rs),
                       decode_seconds=sum(r.get('decode_seconds') or 0 for r in rs),
                       execution_seconds=sum(r.get('execution_seconds') or 0 for r in rs),
                       cold=sum(r.get('cold_state')=='cold' for r in rs), warm=sum(r.get('cold_state')=='warm' for r in rs),
                       errors=dict(Counter(r['status'] for r in rs)))
            rows.append(row)
    out = ROOT/'reports'/run_id
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'summary.json',dict(run_id=run_id,phase=meta['phase'],expected=meta['expected'],completed_records=len(records),cells=rows))
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        w.writerows([{**r,'errors':json.dumps(r['errors'],sort_keys=True)} for r in rows])
    inference = comparisons(identity, cells, config['bootstrap_samples'])
    write_json(out/'paired-tests.json',inference)
    plot(rows,out,meta['phase'])
    lines=[f'# {meta["phase"]} — {run_id}', '',
           'These are actual Ollama outputs. Pilot/smoke estimates are exploratory, not test-set findings.', '',
           f'Planned: {meta["expected"]}; saved complete records: {len(records)}. Accuracy is unavailable when a cell has infrastructure/missing observations; correct/planned then is only a lower bound.', '',
           '| Model | Condition | Correct / planned | Evaluable | Accuracy | Input/output tokens | Generation / execution s |',
           '|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        acc=f'{100*r["accuracy"]:.1f}%' if r['accuracy'] is not None else 'incomplete'
        lines.append(f'| {r["model"]} | {r["condition"]} | {r["correct"]}/{r["planned"]} | {r["evaluable"]} | {acc} | {r["input_tokens"]}/{r["output_tokens"]} | {r["generation_seconds"]:.1f}/{r["execution_seconds"]:.1f} |')
    lines += ['', 'Error distributions, executable-subset accuracy, loading/decode times, cold/warm counts and paired intervals are in summary.json/CSV and paired-tests.json. Executable-subset accuracy is selection-biased. No semantic error or question-subgroup claims are automatically generated.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return dict(output=str(out),cells=rows)


def comparisons(identity, cells, samples):
    expected=set(identity['question_ids'])
    def aligned(model,condition):
        rs=cells.get((model,condition),[])
        mapping={r['question_id']:r for r in rs if r['status'] not in UNAVAILABLE}
        if set(mapping)!=expected:return None
        return np.array([bool(mapping[q].get('correct')) for q in sorted(expected)],dtype=int)
    results=[]
    for model in identity['models']:
        for a,b in CONTRASTS:
            x,y=aligned(model,a),aligned(model,b)
            if x is None or y is None:
                results.append(dict(model=model,a=a,b=b,status='incomplete/no paired inference'))
                continue
            delta,ci=paired_ci(x,y,samples)
            results.append(dict(model=model,a=a,b=b,status='complete',n=len(x),difference=delta,ci95=ci,**mcnemar(x,y)))
    available=[r for r in results if 'p' in r]
    for r,p in zip(available,holm([r['p'] for r in available],family_size=20)):r['holm_p_family20']=p
    interactions=[]
    for small,large in [('lfm2-350m','lfm2-1.2b'),('qwen3-0.6b','qwen3-1.7b')]:
        for a,b in [('K3','K4'),('K8','K7')]:
            arrays=[aligned(m,c) for m,c in [(small,a),(small,b),(large,a),(large,b)]]
            if any(x is None for x in arrays):continue
            sa,sb,la,lb=arrays
            delta,ci=paired_ci(la-lb,sa-sb,samples)
            interactions.append(dict(small=small,large=large,a=a,b=b,difference_in_differences=delta,ci95=ci,p=paired_permutation((la-lb)-(sa-sb),samples)))
    for r,p in zip(interactions,holm([r['p'] for r in interactions],family_size=4)):r['holm_p_family4']=p
    return dict(unit='question',bootstrap_samples=samples,seed=20261021,primary_family_size=20,
                contrasts=results,interaction_family_size=4,interactions=interactions,
                note='No stacking of demonstration pairs. Pilot tests exploratory. CIs are marginal 95%; Holm adjusts tests, not intervals.')


def plot(rows,out,phase):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    models=list(dict.fromkeys(r['model'] for r in rows))
    conditions=list(dict.fromkeys(r['condition'] for r in rows))
    matrix=np.full((len(models),len(conditions)),np.nan)
    for r in rows:
        if r['accuracy'] is not None:matrix[models.index(r['model']),conditions.index(r['condition'])]=r['accuracy']
    fig,ax=plt.subplots(figsize=(max(9,len(conditions)*.7),max(2.5,len(models)*.7)))
    im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    for i in range(len(models)):
        for j in range(len(conditions)):
            v=matrix[i,j];ax.text(j,i,'N/A' if np.isnan(v) else f'{v:.1%}',ha='center',va='center',fontsize=8,color='white' if v>.65 else 'black')
    ax.set_xticks(range(len(conditions)),conditions,rotation=45,ha='right');ax.set_yticks(range(len(models)),models)
    ax.set_title(f'Actual {phase} accuracy — incomplete cells omitted')
    fig.colorbar(im,ax=ax,label='Exact accuracy');fig.tight_layout();fig.savefig(out/'accuracy.png',dpi=180);plt.close(fig)


def estimate(config,run_id=None):
    nmodels=len(config['models'])
    result=dict(test_questions=1319,models=nmodels,main7_generations=1319*nmodels*7,
                controls8_generations=1319*nmodels*8,full15_generations=1319*nmodels*15,
                robustness_B_C_fewshot_generations=1319*nmodels*10*2,pilot_generations=200*nmodels*15)
    if run_id:
        store=Store(ROOT/config['database']);meta=store.metadata(run_id)
        if meta['phase']!='pilot': raise ValueError('Runtime extrapolation requires pilot measurements')
        from .prompts import CONDITIONS
        active_ids={c.id for c in CONDITIONS}
        records=[r for state,r in store.records(run_id) if state=='complete' and r.get('raw_output') is not None and r['condition_id'] in active_ids]
        strata=defaultdict(list)
        for r in records:strata[(r['model_id'],r['condition_id'])].append(r.get('generation_wall_seconds',0)+r.get('execution_seconds',0))
        expected={(m,c['id']) for m in config['models'] for c in meta['identity']['conditions'] if c['id'] in active_ids}
        if set(strata)!=expected:
            result['timing_status']='insufficient model/condition coverage'
        else:
            seconds=1319*sum(np.mean(strata[k]) for k in expected)
            result.update(timing_status='pilot extrapolation, sequential same hardware', estimated_active_hours=float(seconds/3600),
                          sensitivity_hours=[float(seconds*.7/3600),float(seconds*1.5/3600)],
                          sensitivity_note='Planning range (0.7–1.5x), not a statistical CI. Output lengths, cache, thermal throttling, container startup and contention can change runtime.',
                          pilot_generated=len(records),pilot_expected=meta['expected'])
    return result


def review_sample(config,run_id,per_stratum=3):
    store=Store(ROOT/config['database']);meta=store.metadata(run_id)
    records=[r for state,r in store.records(run_id) if state=='complete']
    strata=defaultdict(list)
    for r in records:strata[(r['model_id'],r['condition_id'],r['status'])].append(r)
    rng=random.Random(20261021);sample=[];key=[]
    qs={q.id:q.text for s in ['pilot','test'] for q in GSM8K().questions(s)}
    for stratum,rs in sorted(strata.items()):
        chosen=rng.sample(rs,min(per_stratum,len(rs)))
        for r in chosen:
            rid=digest([run_id,r['question_id'],*stratum])[:16]
            sample.append(dict(review_id=rid,question=qs[r['question_id']],reference_answer=r['gold'],raw_output=r['raw_output'],
                               execution_stdout=(r.get('execution') or {}).get('stdout',''),
                               semantic_modeling_error='',arithmetic_error='',api_error='',state_update_compliance='',uncertain='',reviewer='',rationale=''))
            key.append(dict(review_id=rid,question_id=r['question_id'],stratum=stratum,population=len(rs),sampled=len(chosen),inclusion_probability=len(chosen)/len(rs)))
    rng.shuffle(sample)
    out=ROOT/'reports'/run_id;out.mkdir(parents=True,exist_ok=True)
    with (out/'blinded-review.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(sample[0]));w.writeheader();w.writerows(sample)
    write_json(out/'review-key-private.json',key)
    return str(out/'blinded-review.csv')
