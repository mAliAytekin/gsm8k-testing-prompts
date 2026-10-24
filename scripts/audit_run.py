"""Read-only record/provenance audit; no inference or code execution."""
import json,pathlib,sqlite3,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from gsm8k_lab.common import ROOT,read_json,digest
from gsm8k_lab.data import GSM8K
from gsm8k_lab.parsing import numeric
from gsm8k_lab.store import Store
rid=sys.argv[1]
s=Store(ROOT/'results/experiments.sqlite');meta=s.metadata(rid);records=s.records(rid)
questions={q.id:q for q in GSM8K().questions('pilot')+GSM8K().questions('test')}
gold=read_json(ROOT/'data/gold.json')
checks=0
for state,r in records:
 if state!='complete':continue
 q=questions[r['question_id']]
 assert r['question_hash']==q.sha256
 assert r['prompt'][-1]=={'role':'user','content':q.text}
 assert r['prompt_hash']==digest(r['prompt'])
 assert r['gold']==gold[q.id]
 assert r['model_digest']==meta['identity']['models'][r['model_id']]['digest']
 assert r['condition_id'] in {c['id'] for c in meta['identity']['conditions']}
 if r.get('correct'):
  assert numeric(r['prediction'])==numeric(gold[q.id])
 if r.get('raw_output') is not None:
  assert r['input_tokens'] is not None and r['output_tokens'] is not None
  assert r['raw_output']==r['raw_response']['message']['content']
  assert r['request']['options']==meta['identity']['config']['options']
  assert r['request']['messages']==r['prompt']
  assert r['request']['model']==meta['identity']['models'][r['model_id']]['manifest']['ollama']
  assert r['raw_response']['model']==r['request']['model']
  if r['model_id'].startswith('qwen3'):assert r['request']['think'] is False and not r.get('thinking')
 if r.get('execution') and r['execution'].get('image_id'):
  assert r['execution']['image_id']==meta['identity']['sandbox']['id']
 checks+=1
print(json.dumps({'run_id':rid,'audited_complete_records':checks,'planned':meta['expected'],'passed':True},indent=2))
