import hashlib
import json
import pathlib
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def write_json(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def command(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'error': str(e)}


def environment():
    return dict(timestamp=now(), python=sys.version, platform=platform.platform(),
                machine=platform.machine(), dependencies=command([sys.executable, '-m', 'pip', 'freeze']),
                hardware=command(['sysctl', '-n', 'hw.memsize', 'hw.ncpu', 'machdep.cpu.brand_string']),
                ollama_client=command(['ollama', '--version']),
                docker=command(['docker', 'version', '--format', '{{json .}}']))


def source_hashes():
    paths = list((ROOT / 'gsm8k_lab').glob('*.py')) + list((ROOT / 'prompts/v1').glob('*.txt'))
    paths += list((ROOT / 'sandbox').glob('*')) + [ROOT / 'demonstrations/sets.json', ROOT / 'docs/PROTOCOL.md']
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths if p.is_file()}
