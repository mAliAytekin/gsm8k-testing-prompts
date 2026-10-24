"""Independent protocol after explicit cache-policy change; preserves older runs."""
import csv
import fcntl
import random
import time
from collections import Counter
import numpy as np
from gsm8k_lab.common import ROOT, digest, environment, file_hash, now, read_json, source_hashes, write_json
from gsm8k_lab.data import GSM8K, validate_integrity
from gsm8k_lab.prompts import CONDITIONS, Condition, messages as original_messages
from gsm8k_lab.evaluation import evaluate as original_evaluate
from gsm8k_lab.ollama import Ollama, InfrastructureError
from gsm8k_lab.sandbox import Sandbox
from gsm8k_lab.store import Store
from gsm8k_lab.analysis import UNAVAILABLE, paired_ci, mcnemar, holm
from extensions.sampling import select
from extensions.k9.core import load_examples as teacher_examples, messages as teacher_messages, input_upper_bound

EXTRA = [Condition('K9','K2',1)]
ALL = CONDITIONS+EXTRA


def settings(config_path='configs/repeat10.json'):
    cfg = read_json(ROOT/config_path)
    base = read_json(ROOT/cfg['base_config'])
    base.update(protocol_version=cfg['protocol_version'],database=cfg['database'])
    if cfg['question_count'] not in (10,1000) or cfg['k9_shots']!=1:
        raise ValueError('Unsupported question count or K9 example count')
    return cfg,base


def prompts(q,c,examples):
    if c.id=='K9': return teacher_messages(q,examples['K9'])
    return original_messages(q,c,'A')


def evaluate(r,gold,box):
    return original_evaluate(r,gold,box)


def examples():
    teacher = teacher_examples()
    selected = teacher['examples'][:1]
    if selected[0]['question_id']!='gsm8k:train:00000': raise ValueError('K9 example changed')
    return {'K9':selected},teacher


def hashes(config_path='configs/repeat10.json'):
    paths = [config_path,'extensions/sampling.py','scripts/sample_run.py','configs/model-lock.json','configs/k9.json','docs/REPEAT10_PROTOCOL.md','extensions/repeat10.py',
             'scripts/repeat10.py','extensions/k9/core.py',
             'demonstrations/k9/teacher.json']
    cfg=read_json(ROOT/config_path)
    if 'question_manifest' in cfg:paths.extend([cfg['question_manifest'],'docs/SAMPLE1000_PROTOCOL.md'])
    return {**source_hashes(),**{p:file_hash(ROOT/p) for p in paths}}


def run(resume_id=None,config_path='configs/repeat10.json'):
    cfg,base=settings(config_path); manifest=validate_integrity()
    qs=select(cfg); demos,teacher=examples()
    expected_count=len(qs)*len(ALL)*len(base['models']);prefix='repeat'+str(len(qs))
    client=Ollama(base['ollama_url'],base['request_timeout_seconds'],base['transport_retries'])
    box=Sandbox(base['sandbox_image'],base['sandbox_wall_seconds']); sandbox_info=box.inspect()
    baseline=read_json(ROOT/cfg['model_lock'])
    if digest(manifest)!=baseline['split_manifest_hash']: raise ValueError('Data changed')
    tags={t['name']:t for t in client.tags()}
    models={m['id']:m for m in read_json(ROOT/'configs/models.json')['models']}
    snapshots={}
    for mid in base['models']:
        model=models[mid]; tag=tags[model['ollama']]; show=client.show(model['ollama'])
        if tag['digest']!=baseline['models'][mid]['digest']: raise ValueError('Model digest changed')
        if show['details']['quantization_level']!='Q8_0': raise ValueError('Quantization changed')
        snapshots[mid]=dict(manifest=model,digest=tag['digest'],show=show)
    for q in qs:
        for c in ALL:
            if input_upper_bound(prompts(q,c,demos))+base['options']['num_predict']>base['options']['num_ctx']:
                raise ValueError('Context preflight failed')
    identity=dict(config=cfg,effective_config=base,models=snapshots,sandbox=sandbox_info,
                  conditions=[c.__dict__ for c in ALL],question_ids=[q.id for q in qs],
                  demonstration_hash=digest(demos),teacher=teacher['teacher'],
                  split_manifest_hash=digest(manifest),hashes=hashes(config_path),
                  cache_policy='resident models / configured keep_alive / prompt cache permitted and recorded')
    rid=digest(identity)[:20]
    config_id=digest(identity)
    if resume_id and resume_id!=rid: raise ValueError('Resume identity changed')
    with open(str(ROOT/cfg['database'])+'.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        store=Store(ROOT/cfg['database'])
        store.add_run(rid,dict(id=rid,identity=identity,phase='repeat'+str(cfg['question_count']),created_at=now(),expected=expected_count,
                              environment=environment(),ollama_version=client.request('/api/version')))
        write_json(ROOT/f'artifacts/{prefix}-latest.json',dict(run_id=rid,expected=expected_count,database=cfg['database']))
        print(f'RUN {rid} expected={expected_count}',flush=True)
        store.recover(rid); gold=read_json(ROOT/'data/gold.json')
        for state,r in store.records(rid):
            if state=='generated':store.save(evaluate(r,gold[r['question_id']],box),'complete')
        count=len(store.records(rid))
        for mid in base['models']:
            name=models[mid]['ollama']
            for q in qs:
                ordered=list(ALL)
                random.Random(base['seed']+int(q.id.rsplit(':',1)[1])).shuffle(ordered)
                for c in ordered:
                    prompt=prompts(q,c,demos)
                    r=dict(run_id=rid,config_id=config_id,question_id=q.id,question_hash=q.sha256,
                           model_id=mid,model_digest=snapshots[mid]['digest'],condition_id=c.id,arm=c.arm,
                           shots=c.shots,demo_pair='teacher-first' if c.id=='K9' else 'A' if c.shots else 'none',
                           prompt=prompt,prompt_hash=digest(prompt),created_at=now(),raw_output=None,
                           thinking=None,prediction=None,parsed_output=None,gold=None,error=None,status=None,
                           correct=None,execution=None,execution_seconds=0,generation_wall_seconds=0,
                           load_seconds=0,prompt_seconds=0,decode_seconds=0,input_tokens=None,output_tokens=None,
                           prompt_cached_tokens=None,truncated=False,context_overflow=False,
                           demonstration_hash=identity['demonstration_hash'],cache_policy=identity['cache_policy'])
                    if not store.claim(r):continue
                    start=time.monotonic()
                    try:
                        r['cold_state']='warm' if name in client.loaded() else 'cold'
                        response,request=client.generate(name,prompt,base,qwen=mid.startswith('qwen3'))
                        r.update(request=request,raw_response=response,raw_output=response['message']['content'],
                                 thinking=response['message'].get('thinking'),generation_wall_seconds=time.monotonic()-start,
                                 load_seconds=response.get('load_duration',0)/1e9,
                                 prompt_seconds=response.get('prompt_eval_duration',0)/1e9,
                                 decode_seconds=response.get('eval_duration',0)/1e9,
                                 input_tokens=response.get('prompt_eval_count'),output_tokens=response.get('eval_count'),
                                 prompt_cached_tokens=response.get('prompt_eval_cached_count'),
                                 truncated=response.get('done_reason')=='length' or response.get('eval_count',0)>=base['options']['num_predict'])
                        if r['thinking']:
                            r.update(status='infrastructure_error',error='Unexpected thinking')
                        if (r['input_tokens'] or 0)+(r['output_tokens'] or 0)>=base['options']['num_ctx']:
                            r.update(status='context_overflow',context_overflow=True)
                        store.save(r,'generated'); r=evaluate(r,gold[q.id],box)
                    except InfrastructureError as e:
                        r.update(status='infrastructure_error',error=str(e),gold=gold[q.id],correct=None,
                                 generation_wall_seconds=time.monotonic()-start)
                    store.save(r,'complete'); count+=1
                    if count%10==0: print(f'{count}/{expected_count} {mid} {q.id} {c.id} {r["status"]}',flush=True)
        write_json(ROOT/f'artifacts/{prefix}-completion.json',dict(run_id=rid,recorded=count,expected=expected_count,ended_at=now()))
        print('FINISHED '+rid,flush=True)
    return rid


def analyze(rid,config_path='configs/repeat10.json'):
    cfg,base=settings(config_path);store=Store(ROOT/cfg['database']);meta=store.metadata(rid);i=meta['identity']
    if i['hashes']!=hashes(config_path) or i['config']!=cfg: raise ValueError('Analysis sources/config changed')
    records=[r for state,r in store.records(rid) if state=='complete']
    expected=set(i['question_ids']);demos,_=examples();qmap={q.id:q for q in select(cfg)}
    n=cfg['question_count'];expected_count=n*len(ALL)*len(base['models'])
    gold=read_json(ROOT/'data/gold.json');rows=[];contrasts=[]
    for r in records:
        c=next(c for c in ALL if c.id==r['condition_id']);p=prompts(qmap[r['question_id']],c,demos)
        assert r['prompt']==p and r['prompt_hash']==digest(p) and r['shots']==c.shots
        assert r['question_hash']==qmap[r['question_id']].sha256
        assert r['model_digest']==i['models'][r['model_id']]['digest']
        if r.get('raw_output') is not None:
            assert r['request']['messages']==p and r['request']['keep_alive']==base['keep_alive']
            assert r['request']['options']==base['options']
            assert r['raw_response']['message']['content']==r['raw_output']
            if r['model_id'].startswith('qwen3'):assert r['request']['think'] is False
    cells={}
    for mid in i['models']:
        for c in ALL:
            rs=[r for r in records if r['model_id']==mid and r['condition_id']==c.id]
            usable=[r for r in rs if r['status'] not in UNAVAILABLE]
            cells[mid,c.id]={r['question_id']:r for r in usable}
            complete=set(cells[mid,c.id])==expected
            executable=[r for r in usable if r.get('executable')]
            correct=sum(r.get('correct') is True for r in rs)
            row=dict(model=mid,condition=c.id,shots=c.shots,planned=len(expected),recorded=len(rs),
                     evaluable=len(usable),complete=complete,missing=len(expected)-len(rs),correct=correct,
                     accuracy=correct/len(expected) if complete else None,
                     accuracy_lower_bound=correct/len(expected),parseable=sum(bool(r.get('parseable')) for r in usable),
                     executable=len(executable),accuracy_executable_selected=sum(bool(r['correct']) for r in executable)/len(executable) if executable else None,
                     errors=dict(Counter(r['status'] for r in rs)),cold=sum(r.get('cold_state')=='cold' for r in rs),
                     warm=sum(r.get('cold_state')=='warm' for r in rs))
            for key in ['input_tokens','output_tokens','generation_wall_seconds','load_seconds','prompt_seconds','decode_seconds','execution_seconds','prompt_cached_tokens']:
                row[key]=sum(r.get(key) or 0 for r in rs)
            rows.append(row)
        for a,b in [('K9','K2_1shot')]:
            aa,bb=cells[mid,a],cells[mid,b]
            if set(aa)!=expected or set(bb)!=expected:continue
            ids=sorted(expected);x=[bool(aa[q]['correct']) for q in ids];y=[bool(bb[q]['correct']) for q in ids]
            delta,ci=paired_ci(x,y,cfg['bootstrap_samples'])
            contrasts.append(dict(model=mid,a=a,b=b,n=len(ids),difference=delta,ci95=ci,**mcnemar(x,y)))
    for c,p in zip(contrasts,holm([c['p'] for c in contrasts],family_size=5)):c['holm_p_family5']=p
    out=ROOT/'reports'/rid;out.mkdir(parents=True,exist_ok=True)
    write_json(out/'summary.json',dict(run_id=rid,expected=expected_count,completed_records=len(records),phase='repeat'+str(cfg['question_count']),
                                     cells=rows,contrasts=contrasts,question_ids=i['question_ids'],
                                     unit='question',exploratory=True,bootstrap_samples=10000))
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write_json(out/'audit.json',dict(passed=True,audited_records=len(records),
               cached_tokens=sum(r.get('prompt_cached_tokens') or 0 for r in records),
               missing_cached_counts=sum(r.get('raw_output') is not None and r.get('prompt_cached_tokens') is None for r in records)))
    models=list(i['models']);lines=[f'# {n} soruda tüm koşulların tekrarı','',f'Koşum `{rid}`. Planlanan {expected_count}; tamamlanan {len(records)}.',
        '', 'Sabit manifestteki aynı sorular; beş Q8_0 model; modeller bellekte tutulur, prompt cache kullanımına izin verilir. K9 yalnızca ilk Gemma4:26b-mlx örneğini içerir.',
        '', f'**Her hücre {n} soruya dayanır; bir soru {100/n:g} yüzde puandır. Bulgular keşifseldir.**',
        '', '| Koşul | '+' | '.join(models)+' |','|---|'+'---:|'*len(models)]
    for c in ALL:
        vals=[]
        for mid in models:
            r=next(r for r in rows if r['model']==mid and r['condition']==c.id)
            vals.append(f'{r["correct"]}/{n}' if r['complete'] else 'eksik')
        lines.append('| '+c.id+' | '+' | '.join(vals)+' |')
    errors=Counter(r['status'] for r in records)
    lines+=['',f'Hata/sonuç dağılımı: {dict(errors)}.',
            '',f'Giriş/çıkış tokenları: {sum(r.get("input_tokens") or 0 for r in records)} / {sum(r.get("output_tokens") or 0 for r in records)}.',
            '',f'Üretim duvar süresi: {sum(r["generation_wall_seconds"] for r in records):.1f} s; model yükleme bunun içinde ayrıca {sum(r["load_seconds"] for r in records):.1f} s. İzole yürütme/yorumlama: {sum(r["execution_seconds"] for r in records):.1f} s.',
            '', 'K9 ile eski dört örnekli K9 arasında cache, örnek sayısı ve çalışma zamanı değiştiği için tek faktör etkisi iddia edilemez. Çalıştırılabilir alt küme doğruluğu seçilmiş bir alt kümedir. Eşleştirilmiş keşifsel testler, hata dağılımları, yükleme/prefill/decode süreleri ve tokenlar summary.json/CSV içindedir. Tam test çalıştırılmadı.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matrix=np.array([[next(r['accuracy'] if r['accuracy'] is not None else np.nan for r in rows if r['model']==mid and r['condition']==c.id) for c in ALL] for mid in models])
    fig,ax=plt.subplots(figsize=(14,5));im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    for y in range(len(models)):
        for x in range(len(ALL)):
            v=matrix[y,x];ax.text(x,y,'N/A' if np.isnan(v) else f'{100*v:.0f}',ha='center',va='center',fontsize=8,color='white' if v>.65 else 'black')
    ax.set_xticks(range(len(ALL)),[c.id for c in ALL],rotation=45,ha='right');ax.set_yticks(range(len(models)),models)
    ax.set_title(f'Actual repeat: {n} questions / cell, resident models, cache permitted, K9 one-shot');fig.colorbar(im,ax=ax,label='Accuracy')
    fig.tight_layout();fig.savefig(out/'accuracy.png',dpi=180);plt.close(fig)
    print(out,flush=True)
    return out
