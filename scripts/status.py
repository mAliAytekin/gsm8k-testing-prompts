"""Read-only pilot progress, without claiming incomplete results are final."""
import collections,json,pathlib,sqlite3
root=pathlib.Path(__file__).resolve().parents[1]
latest=json.loads((root/'artifacts/pilot-latest.json').read_text())
con=sqlite3.connect('file:'+str(root/latest['database'])+'?mode=ro',uri=True)
records=[json.loads(x[0]) for x in con.execute('SELECT record FROM records WHERE run_id=? AND state="complete"',(latest['run_id'],))]
print(json.dumps({'run_id':latest['run_id'],'completed':len(records),'expected':latest['expected'],'by_model':dict(collections.Counter(r['model_id'] for r in records)),'status_counts':dict(collections.Counter(r['status'] for r in records)),'measured_seconds':round(sum(r.get('generation_wall_seconds',0)+r.get('execution_seconds',0) for r in records),1)},indent=2))
