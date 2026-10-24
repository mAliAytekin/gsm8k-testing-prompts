"""Pinned publisher GGUFs, verified sizes/SHA256, explicit local Ollama aliases."""
import hashlib,json,pathlib,shutil,subprocess,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def main():
 entries=[]
 for repo in ['LiquidAI/LFM2-350M-GGUF','LiquidAI/LFM2-700M-GGUF','LiquidAI/LFM2-1.2B-GGUF','Qwen/Qwen3-0.6B-GGUF','Qwen/Qwen3-1.7B-GGUF']:
  meta=json.loads((ROOT/'sources'/(repo.replace('/','__')+'.json')).read_text())
  f=next(x for x in meta['siblings'] if x['rfilename'].lower().endswith('q8_0.gguf'))
  name=repo.split('/')[1].removesuffix('-GGUF')
  entries.append(dict(id=name.lower(),name=name,source='https://huggingface.co/'+repo,model_card='https://huggingface.co/'+repo.removesuffix('-GGUF'),revision=meta['sha'],filename=f['rfilename'],size=f['size'],sha256=f['lfs']['sha256'],quantization='Q8_0',ollama='gsm8k-'+name.lower()+':q8_0',origin='official publisher GGUF; explicitly local alias, not a registry tag'))
 total=sum(e['size'] for e in entries)
 free=shutil.disk_usage(ROOT).free
 print(json.dumps({'download_bytes':total,'free_bytes':free,'required_with_import_copy':total*2+5*1024**3}),flush=True)
 if free < total*2+5*1024**3: raise SystemExit('Insufficient free disk')
 manifest={'models':entries,'verified_on':'2026-10-21','choice':'Publisher Q8_0 for all five targets; no substitution. Registry qwen3:0.6b-q8_0 and qwen3:1.7b-q8_0 exist but publisher GGUFs selected for uniform provenance.'}
 (ROOT/'configs/models.json').write_text(json.dumps(manifest,indent=2)+'\n')
 for e in entries:
  dest=ROOT/'models'/e['filename'];url=e['source']+'/resolve/'+e['revision']+'/'+e['filename']
  if not dest.exists() or dest.stat().st_size!=e['size'] or sha(dest)!=e['sha256']:
   part=dest.with_suffix('.part')
   subprocess.run(['curl','--fail','--location','--retry','3','--continue-at','-','--output',str(part),url],check=True)
   if part.stat().st_size!=e['size'] or sha(part)!=e['sha256']: raise RuntimeError('GGUF integrity failure '+str(part))
   part.rename(dest)
  mf=ROOT/'models'/(e['id']+'.Modelfile')
  mf.write_text('FROM '+str(dest)+'\nPARAMETER num_ctx 4096\n')
  subprocess.run(['ollama','create',e['ollama'],'-f',str(mf)],check=True)
  req=urllib.request.Request('http://127.0.0.1:11434/api/show',json.dumps({'model':e['ollama']}).encode(),{'Content-Type':'application/json'})
  show=json.load(urllib.request.urlopen(req));(ROOT/'sources'/(e['id']+'-ollama-show.json')).write_text(json.dumps(show,indent=2))
  if show['details']['quantization_level']!='Q8_0': raise RuntimeError('Quantization mismatch')
  print('READY',e['id'],flush=True)
 tags=json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/tags'))
 (ROOT/'sources/ollama-tags.json').write_text(json.dumps(tags,indent=2))
if __name__=='__main__':main()
