"""Actual isolation tests, no mocked Docker and no host generated-code execution."""
import os
import pytest
from gsm8k_lab.sandbox import Sandbox,SandboxUnavailable

pytestmark=pytest.mark.integration

@pytest.fixture(scope='module')
def box():
    if os.environ.get('GSM8K_DOCKER_TESTS')!='1':pytest.skip('Set GSM8K_DOCKER_TESTS=1 for real Docker tests')
    b=Sandbox('gsm8k-sandbox:py3.12.8-sympy1.13.3')
    b.inspect()  # explicitly requested integration tests MUST fail if unavailable
    return b

def test_real_python_sympy(box):
    r=box.run('import sys, sympy\nassert sys.version_info[:3] == (3,12,8)\nassert sympy.__version__ == "1.13.3"\nprint("FINAL:", sympy.Rational(1,2)+sympy.Rational(1,2))')
    assert r['returncode']==0 and r['stdout']=='FINAL: 1\n'

def test_python_annotation_is_not_a_printed_answer(box):
    from gsm8k_lab.evaluation import evaluate
    # This is legal Python syntax, but prints nothing. Never parse a scalar
    # directly from model source as if it had been produced by execution.
    r=evaluate({'raw_output':'FINAL: 30','arm':'K4'},'30',box)
    assert r['execution']['returncode']==0 and r['execution']['stdout']==''
    assert r['status']=='format_error' and r['correct'] is False

def test_network_files_and_privileges(box):
    r=box.run('''import os, socket
assert os.getuid() == 65534
assert not os.path.exists('/Users')
assert not os.path.exists('/var/run/docker.sock')
assert not os.path.exists('/workspace')
assert 'OPENAI_API_KEY' not in os.environ
try:
    open('/opt/escape','w')
except OSError:
    pass
else:
    raise AssertionError('Writable root filesystem')
try:
    socket.create_connection(('1.1.1.1',80),timeout=.2)
except OSError:
    pass
else:
    raise AssertionError('Network reachable')
print('FINAL: 1')''')
    assert r['returncode']==0,r

def test_cpu_timeout(box):
    r=box.run('while True: pass')
    assert r['status']=='resource_limit' and r['wall_seconds']<15

def test_memory_limit(box):
    r=box.run('x = bytearray(1024**3)')
    assert r['status']=='resource_limit'

def test_output_limit(box):
    r=box.run('while True: print("x"*4096)')
    assert r['status']=='resource_limit' and len(r['stdout'])<=65536

def test_direct_container_stdout_bounded(box):
    r=box.run('import os\nf=os.open("/proc/1/fd/1",os.O_WRONLY)\nwhile True: os.write(f,b"x"*16384)')
    assert r['status']=='resource_limit'

def test_process_limit(box):
    r=box.run('''import subprocess
children=[]
try:
    for i in range(100):
        children.append(subprocess.Popen(['sleep','10']))
except OSError:
    print('FINAL: 1')
finally:
    for p in children: p.kill(); p.wait()
''')
    assert r['returncode']==0 and r['stdout']=='FINAL: 1\n',r

def test_tmpfs_size_limit(box):
    r=box.run('''import os
try:
    for i in range(400):
        with open('/tmp/f'+str(i),'wb') as f: f.write(b'x'*60000)
except OSError:
    print('FINAL: 1')
else:
    raise AssertionError('Temporary storage not bounded')
''')
    assert r['status']=='resource_limit',r
