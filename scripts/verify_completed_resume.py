"""Verify a completed real run is unchanged by the actual resume command."""
import hashlib
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from gsm8k_lab.common import ROOT, now, read_json, write_json
from gsm8k_lab.store import Store

run_id = sys.argv[1]
config = read_json(ROOT / 'configs/experiment.json')
store = Store(ROOT / config['database'])
metadata = store.metadata(run_id)


def snapshot():
    rows = store.db.execute(
        'SELECT state,record FROM records WHERE run_id=? '
        'ORDER BY question_id,model_id,condition_id,demo_pair', (run_id,)
    ).fetchall()
    assert len(rows) == metadata['expected']
    assert all(state == 'complete' for state, _ in rows)
    payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()
    return {'count': len(rows), 'records_sha256': hashlib.sha256(payload).hexdigest()}


before = snapshot()
process = subprocess.run(
    [sys.executable, '-m', 'gsm8k_lab', 'resume', run_id],
    cwd=ROOT, capture_output=True, text=True, timeout=300, check=True,
)
after = snapshot()
assert before == after, 'Resume modified completed records'
artifact = {
    'run_id': run_id, 'verified_at': now(), 'before': before, 'after': after,
    'identical': True, 'resume_stdout': process.stdout, 'resume_stderr': process.stderr,
    'note': 'Actual CLI resume; all completed serialized records stayed identical.',
}
write_json(ROOT / 'artifacts/resume-validation.json', artifact)
print(json.dumps({'run_id': run_id, 'identical': True, **after}, indent=2))
