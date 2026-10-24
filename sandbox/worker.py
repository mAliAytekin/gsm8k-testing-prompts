"""Runs ONLY inside the constrained container; never import on the host."""
import json,os,resource,subprocess,sys,tempfile,time
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
job=json.loads(sys.stdin.buffer.read(65537))
code=job['code']
if len(code.encode())>60000: raise ValueError('Code too large')
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(3,4))
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
 resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536))
 resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
 resource.setrlimit(resource.RLIMIT_NPROC,(24,24))
with tempfile.TemporaryDirectory() as d:
 path=d+'/solution.py';open(path,'w').write(code)
 start=time.monotonic()
 with open(d+'/stdout','wb') as out,open(d+'/stderr','wb') as err:
  p=subprocess.Popen([sys.executable,'-I',path],stdout=out,stderr=err,stdin=subprocess.DEVNULL,preexec_fn=limits,start_new_session=True,env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1','HOME':'/tmp'})
  status='finished'
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:
   status='resource_limit';os.killpg(p.pid,9);p.wait()
 stdout=open(d+'/stdout','rb').read(65536).decode('utf-8','replace');stderr=open(d+'/stderr','rb').read(65536).decode('utf-8','replace')
 fs=os.statvfs('/tmp')
 if p.returncode in [-9,-24,-25] or len(stdout.encode())>=65536 or len(stderr.encode())>=65536 or 'MemoryError' in stderr or fs.f_bavail*fs.f_frsize < 65536:status='resource_limit'
 print(json.dumps(dict(stdout=stdout,stderr=stderr,returncode=p.returncode,status=status,code_seconds=time.monotonic()-start)))
