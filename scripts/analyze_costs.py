"""Descriptive observed cold/warm costs and pilot-based planning estimates."""
import csv,pathlib,sys,statistics
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from collections import defaultdict
from gsm8k_lab.common import ROOT,read_json,write_json,file_hash,now
from gsm8k_lab.store import Store
from gsm8k_lab.analysis import UNAVAILABLE
from gsm8k_lab.prompts import MAIN,CONTROLS,CONDITIONS
config=read_json(ROOT/'configs/experiment.json');rid=sys.argv[1]
s=Store(ROOT/config['database']);meta=s.metadata(rid)
records=[r for state,r in s.records(rid) if state=='complete' and r.get('raw_output') is not None]
strata=defaultdict(list)
for r in records:strata[r['model_id'],r['condition_id'],r.get('cold_state','unknown')].append(r)
rows=[]
def mean(xs):return statistics.mean(xs) if xs else None
for (model,condition,state),rs in sorted(strata.items()):
 gen=sorted(r['generation_wall_seconds'] for r in rs)
 executed=[r for r in rs if r.get('execution')]
 rows.append(dict(model=model,condition=condition,cold_state=state,n=len(rs),generation_mean_s=mean(gen),
                  generation_median_s=statistics.median(gen),generation_p95_observed_s=gen[min(len(gen)-1,int(.95*(len(gen)-1)))],
                  load_mean_s=mean([r['load_seconds'] for r in rs]),prompt_mean_s=mean([r['prompt_seconds'] for r in rs]),
                  decode_mean_s=mean([r['decode_seconds'] for r in rs]),input_tokens_mean=mean([r['input_tokens'] for r in rs]),
                  output_tokens_mean=mean([r['output_tokens'] for r in rs]),execution_wall_mean_s=mean([r['execution_seconds'] for r in rs]),
                  code_jobs=len(executed),python_seconds_mean_executed=mean([r['execution']['code_seconds'] for r in executed if 'code_seconds' in r['execution']]),
                  container_overhead_mean_executed_s=mean([r['execution_seconds']-r['execution']['code_seconds'] for r in executed if 'code_seconds' in r['execution']])))
out=ROOT/'reports'/rid;out.mkdir(parents=True,exist_ok=True)
with (out/'cold-warm-costs.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
planning={}
if meta['phase']=='pilot':
 cell_times=defaultdict(list)
 for r in records:
  if r['status'] not in UNAVAILABLE:
   cell_times[r['model_id'],r['condition_id']].append(r['generation_wall_seconds']+r['execution_seconds'])
 models=list(meta['identity']['models'])
 groups={'primary7':([c.id for c in MAIN],1),'controls8':([c.id for c in CONTROLS],1),
         'primary_and_controls15':([c.id for c in CONDITIONS],1),
         'robustness_B_C_20':([c.id for c in CONDITIONS if c.shots],2)}
 for name,(conditions,repeats) in groups.items():
  keys=[(m,c) for m in models for c in conditions]
  complete=all(len(cell_times[k])==200 for k in keys)
  row=dict(generations=1319*len(keys)*repeats,complete_pilot_coverage=complete)
  if complete:
   hours=1319*repeats*sum(mean(cell_times[k]) for k in keys)/3600
   row.update(hours=hours,planning_range_hours=[.7*hours,1.5*hours])
  planning[name]=row
 if all('hours' in planning[g] for g in ['primary_and_controls15','robustness_B_C_20']):
  h=planning['primary_and_controls15']['hours']+planning['robustness_B_C_20']['hours']
  planning['all_A_B_C']=dict(generations=1319*len(models)*(len(CONDITIONS)+2*sum(c.shots>0 for c in CONDITIONS)),hours=h,planning_range_hours=[.7*h,1.5*h])
write_json(out/'cost-planning.json',dict(run_id=rid,created_at=now(),script_sha256=file_hash(__file__),
           cold_warm_note='Observed residency from /api/ps, not controlled cold-cache trials. Missing cold strata means no cold observation, not zero loading cost.',
           timing_note='Generation client wall already includes load/prefill/decode; execution wall includes container startup. Do not double-count load.',
           uncertainty='0.7–1.5x planning range, not a confidence interval. Robustness uses pair A few-shot timings as a proxy for B/C; lengths/content/cache may differ. No setup/download/reporting time included.',
           plans=planning))
print(out/'cold-warm-costs.csv');print(out/'cost-planning.json')
