"""Use primary zero-shot observations as shared baselines, never resample them.
Usage: python scripts/compare_robustness.py PRIMARY_RUN ROBUSTNESS_RUN
"""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from collections import defaultdict
from gsm8k_lab.common import ROOT,read_json,write_json
from gsm8k_lab.analysis import comparisons,UNAVAILABLE
from gsm8k_lab.store import Store
config=read_json(ROOT/'configs/experiment.json')
s=Store(ROOT/config['database'])
primary,robust=sys.argv[1:3]
a,b=s.metadata(primary),s.metadata(robust)
assert a['phase']=='main' and b['phase']=='robustness'
ia,ib=a['identity'],b['identity']
for key in ['config','models','question_ids','split_manifest_hash','hashes','sandbox']:
 assert ia[key]==ib[key],f'Incomparable run identity: {key}'
assert ia['demonstration_pair']=='A' and ib['demonstration_pair'] in ('B','C')
cells=defaultdict(list)
for rid,keep_zero in [(primary,True),(robust,False)]:
 for state,r in s.records(rid):
  if state=='complete' and ((r['shots']==0)==keep_zero):
   cells[r['model_id'],r['condition_id']].append(r)
result=comparisons(ib,cells,config['bootstrap_samples'])
result.update(primary_run=primary,robustness_run=robust,pair=ib['demonstration_pair'],baseline_policy='Reuse the same primary zero-shot observations; these are shared baselines, not independent replicates. Analyze each pair separately.')
out=ROOT/'reports'/robust/'paired-tests-shared-baseline.json'
write_json(out,result);print(out)
