import argparse,json,subprocess,sys
from .common import ROOT,digest,environment,read_json,source_hashes,write_json,now
from .runner import run,make_client,execute_pending
from .sandbox import Sandbox
from .store import Store

def main():
 p=argparse.ArgumentParser(description='Reproducible local Ollama GSM8K experiments')
 p.add_argument('--config',default=str(ROOT/'configs/experiment.json'))
 sub=p.add_subparsers(dest='cmd',required=True)
 for name in ['check','prepare-models','prepare-data','verify-demos']:
  sub.add_parser(name)
 for name in ['smoke','pilot','main','controls','robustness']:
  s=sub.add_parser(name);s.add_argument('--models',nargs='+');s.add_argument('--generate-only',action='store_true')
  s.add_argument('--group',choices=['all','main','controls','fewshot'],default='all');s.add_argument('--pair',choices=['A','B','C'],default=None)
  if name=='smoke':s.add_argument('--questions',type=int,default=2)
  if name=='controls':s.add_argument('--split',choices=['pilot','test'],default='pilot')
 for name in ['resume','execute','analyze','review','freeze']:
  s=sub.add_parser(name);s.add_argument('run_id')
 s=sub.add_parser('estimate');s.add_argument('--pilot-run')
 args=p.parse_args();config=read_json(args.config)
 if args.cmd=='check':
  env=environment();client=make_client(config)
  try:env.update(ollama_version=client.request('/api/version'),models=client.tags())
  except Exception as e:env['ollama_error']=str(e)
  try:env['sandbox']=Sandbox(config['sandbox_image']).inspect()
  except Exception as e:env['sandbox_error']=str(e)
  write_json(ROOT/'artifacts/environment.json',env);print(json.dumps(env,indent=2))
 elif args.cmd=='prepare-models':subprocess.run([sys.executable,str(ROOT/'scripts/prepare_models.py')],check=True)
 elif args.cmd=='prepare-data':
  from .data import prepare
  m=prepare();print(json.dumps({k:v for k,v in m.items() if k!='ids'},indent=2))
 elif args.cmd=='verify-demos':
  from .parsing import numeric,arithmetic,code_output,answer_field
  box=Sandbox(config['sandbox_image']);checks=[]
  for pair,ds in read_json(ROOT/'demonstrations/sets.json')['pairs'].items():
   for d in ds:
    assert arithmetic(d['solutions']['K3'])==numeric(d['answer'])
    assert answer_field(d['solutions']['K2'])==numeric(d['answer'])
    for arm in ['K4','K5','K6']:
     r=box.run(d['solutions'][arm]);ok=r.get('returncode')==0 and code_output(r['stdout'])==numeric(d['answer'])
     checks.append(dict(pair=pair,index=d['train_index'],arm=arm,passed=ok,result=r));assert ok,r
  write_json(ROOT/'artifacts/demonstration-validation.json',checks);print('18 isolated code demonstrations and 12 text/expression solutions verified')
 elif args.cmd in ['smoke','pilot','main','controls','robustness']:
  phase=args.cmd;group=args.group
  if phase=='controls':phase='main' if args.split=='test' else 'pilot';group='controls'
  if phase=='robustness':group='fewshot'
  print(run(config,phase,args.models,group,args.pair,getattr(args,'questions',None),args.generate_only))
 elif args.cmd=='resume':
  meta=Store(ROOT/config['database']).metadata(args.run_id);i=meta['identity']
  ids={c['id'] for c in i['conditions']}
  from .prompts import MAIN,CONTROLS,CONDITIONS
  groups={'all':CONDITIONS,'main':MAIN,'controls':CONTROLS,'fewshot':[c for c in CONDITIONS if c.shots]}
  group=next(k for k,v in groups.items() if {c.id for c in v}==ids)
  print(run(i['config'],i['phase'],list(i['models']),group,i['demonstration_pair'],len(i['question_ids']) if i['phase']=='smoke' else None,i['generate_only'],args.run_id))
 elif args.cmd=='execute':execute_pending(config,args.run_id)
 elif args.cmd=='analyze':
  from .analysis import summarize
  print(summarize(config,args.run_id)['output'])
 elif args.cmd=='estimate':
  from .analysis import estimate
  result=estimate(config,args.pilot_run);write_json(ROOT/'reports/runtime-estimate.json',result);print(json.dumps(result,indent=2))
 elif args.cmd=='review':
  from .analysis import review_sample
  print(review_sample(config,args.run_id))
 elif args.cmd=='freeze':
  store=Store(ROOT/config['database']);meta=store.metadata(args.run_id);records=store.records(args.run_id)
  from .analysis import UNAVAILABLE
  if meta['phase']!='pilot' or len(meta['identity']['question_ids'])!=200:raise ValueError('A 200-question pilot is required')
  if len(records)!=meta['expected'] or any(s!='complete' or r['status'] in UNAVAILABLE for s,r in records):raise ValueError('Pilot incomplete: cannot freeze')
  from .prompts import CONDITIONS
  if set(meta['identity']['models'])!=set(config['models']) or {c['id'] for c in meta['identity']['conditions']}!={c.id for c in CONDITIONS}:raise ValueError('Freeze requires all configured models and all active base conditions')
  if meta['identity']['config']!=config:raise ValueError('Configuration changed since pilot')
  if meta['identity']['hashes']!=source_hashes():raise ValueError('Sources changed since pilot: revalidate under a new run identity')
  frozen=dict(frozen_at=now(),pilot_run=args.run_id,config_hash=digest(config),hashes=source_hashes(),model_digests={k:v['digest'] for k,v in meta['identity']['models'].items()},sandbox=meta['identity']['sandbox'])
  write_json(ROOT/'configs/frozen-protocol.json',frozen);print('Protocol frozen; no test generation started')

if __name__=='__main__':main()
