"""Import the user's requested openai/gsm8k main source, pinned and hash verified.
Run in the separate data-preparation environment (requirements-data.txt).
The resulting JSONL bytes are exactly the already-pinned canonical GSM8K bytes.
"""
import hashlib,json,pathlib,subprocess
import pyarrow.parquet as pq
ROOT=pathlib.Path(__file__).resolve().parents[1]
REVISION='740312add88f781978c0658806c59bc2815b9866'
FILES={
 'train':('ea82612ea9582142387730c793eb67d3b12849002bc0b7fa6f8efafa7351419d','17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465',7473),
 'test':('ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59','3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14',1319)
}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 cache=ROOT/'data/huggingface';cache.mkdir(parents=True,exist_ok=True)
 raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
 checked=[];contents={}
 for split,(parquet_sha,jsonl_sha,count) in FILES.items():
  path=cache/(split+'.parquet')
  url=f'https://huggingface.co/datasets/openai/gsm8k/resolve/{REVISION}/main/{split}-00000-of-00001.parquet'
  if not path.exists() or sha(path.read_bytes())!=parquet_sha:
   subprocess.run(['curl','-fLsS','--retry','3','--max-time','120','-o',str(path),url],check=True)
  if sha(path.read_bytes())!=parquet_sha:raise ValueError('HF parquet SHA256 mismatch')
  rows=pq.read_table(path).to_pylist()
  if len(rows)!=count or any(set(r)!={'question','answer'} for r in rows):raise ValueError('HF schema/count mismatch')
  contents[split]=''.join(json.dumps(r,ensure_ascii=True)+'\n' for r in rows).encode()
  if sha(contents[split])!=jsonl_sha:raise ValueError('Canonical data content changed')
  old=raw/(split+'.jsonl')
  if old.exists() and old.read_bytes()!=contents[split]:raise ValueError('Existing data differs: refusing silent replacement')
  checked.append(dict(split=split,rows=count,url=url,parquet_sha256=parquet_sha,jsonl_sha256=jsonl_sha))
 for split,content in contents.items():
  target=raw/(split+'.jsonl');tmp=target.with_suffix('.tmp');tmp.write_bytes(content);tmp.replace(target)
 manifest=dict(dataset='openai/gsm8k',source='https://huggingface.co/datasets/openai/gsm8k',config='main',revision=REVISION,files=checked,serialization='json.dumps(ensure_ascii=True) plus newline; identical canonical JSONL bytes',pyarrow_version=__import__('pyarrow').__version__)
 (ROOT/'data/huggingface-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
