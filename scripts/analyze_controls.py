"""Exploratory paired shot/control effects; distinct from primary inference.
Usage: python scripts/analyze_controls.py RUN_ID
"""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from collections import defaultdict
import numpy as np
from gsm8k_lab.common import ROOT,read_json,write_json,file_hash,now
from gsm8k_lab.store import Store
from gsm8k_lab.analysis import UNAVAILABLE,paired_ci,mcnemar,holm,paired_permutation
config=read_json(ROOT/'configs/experiment.json');rid=sys.argv[1]
s=Store(ROOT/config['database']);meta=s.metadata(rid)
questions=sorted(meta['identity']['question_ids']);cells=defaultdict(dict)
for state,r in s.records(rid):
 if state=='complete' and r['status'] not in UNAVAILABLE:
  key=(r['model_id'],r['condition_id'])
  if r['question_id'] in cells[key]:raise ValueError('Repeated question inside condition')
  cells[key][r['question_id']]=int(bool(r.get('correct')))
def aligned(model,condition):
 cell=cells[model,condition]
 return np.array([cell[q] for q in questions]) if set(cell)==set(questions) else None
shot_results=[];relative_results=[]
for model in meta['identity']['models']:
 for arm in ['K2','K3','K4','K5']:
  names=[arm,arm+'_1shot',arm+'_2shot']
  for previous,current in [(0,1),(1,2)]:
   a,b=aligned(model,names[current]),aligned(model,names[previous])
   base=dict(model=model,arm=arm,transition=f'{previous}-to-{current}',exploratory=True)
   if a is None or b is None:
    shot_results.append({**base,'status':'incomplete/no paired inference'});continue
   d,ci=paired_ci(a,b,config['bootstrap_samples'])
   shot_results.append({**base,'status':'complete','n':len(a),'difference':d,'ci95':ci,**mcnemar(a,b)})
   sym_names=['K6','K7','K8']
   sa,sb=aligned(model,sym_names[current]),aligned(model,sym_names[previous])
   if sa is None or sb is None:continue
   sym_gain=sa-sb;control_gain=a-b
   d,ci=paired_ci(sym_gain,control_gain,config['bootstrap_samples'])
   relative_results.append({**base,'n':len(a),'sympy_gain_minus_control_gain':d,'ci95':ci,'p':paired_permutation(sym_gain-control_gain,config['bootstrap_samples'])})
valid=[r for r in shot_results if 'p' in r]
for r,p in zip(valid,holm([r['p'] for r in valid],40)):r['holm_p_exploratory_family40']=p
for r,p in zip(relative_results,holm([r['p'] for r in relative_results],40)):r['holm_p_exploratory_family40']=p
out=ROOT/'reports'/rid/'exploratory-controls.json'
write_json(out,dict(run_id=rid,created_at=now(),analysis_script_sha256=file_hash(__file__),unit='question',
                   classification='Exploratory; not part of the 20 primary tests or 4 primary interaction tests.',
                   interpretation='The difference of shot gains does not isolate API teaching causally; examples also change semantic content, representation and prompt length. Do not pool demonstration pairs or repeated runs.',
                   shot_effects=shot_results,relative_sympy_shot_effects=relative_results))
print(out)
