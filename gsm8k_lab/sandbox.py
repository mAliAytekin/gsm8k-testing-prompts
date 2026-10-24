"""Docker VM/container isolation is mandatory; no host execution fallback."""
import json
import os
import selectors
import subprocess
import time
import uuid
from .common import command


class SandboxUnavailable(RuntimeError):
    pass


class Sandbox:
    def __init__(self, image, wall_seconds=15):
        self.image, self.wall_seconds = image, wall_seconds

    def inspect(self):
        info = command(['docker', 'image', 'inspect', self.image])
        if info.get('returncode') != 0:
            raise SandboxUnavailable('Docker daemon or pinned sandbox image unavailable')
        entry = json.loads(info['stdout'])[0]
        return {'id': entry['Id'], 'repo_digests': entry.get('RepoDigests'), 'architecture': entry['Architecture']}

    def run(self, code):
        image_id = self.inspect()['id']
        name = 'gsm8k-job-' + uuid.uuid4().hex
        args = ['docker', 'run', '--rm', '--name', name, '--network=none', '--read-only',
                '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=65534:65534',
                '--pids-limit=32', '--memory=768m', '--memory-swap=768m', '--cpus=1',
                '--ulimit=nofile=64:64', '--ulimit=fsize=65536:65536', '--ulimit=core=0:0',
                '--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777', '--log-driver=none',
                '-i', image_id]
        start = time.monotonic()
        try:
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.stdin.write(json.dumps({'code': code}).encode())
            p.stdin.close()
            buffers = {'stdout': bytearray(), 'stderr': bytearray()}
            selector = selectors.DefaultSelector()
            selector.register(p.stdout, selectors.EVENT_READ, 'stdout')
            selector.register(p.stderr, selectors.EVENT_READ, 'stderr')
            limited = False
            try:
                while selector.get_map():
                    if time.monotonic()-start >= self.wall_seconds:
                        limited = True
                        break
                    for key, _ in selector.select(timeout=.1):
                        chunk = os.read(key.fileobj.fileno(), 16384)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffers[key.data].extend(chunk)
                        if sum(map(len, buffers.values())) > 1024*1024:
                            limited = True
                            break
                    if limited: break
            finally:
                selector.close()
            if limited:
                p.kill(); p.wait(timeout=5)
                return dict(status='resource_limit', stdout='', stderr='Container wall/output limit',
                            returncode=None, wall_seconds=time.monotonic()-start, image_id=image_id)
            p.wait(timeout=2)
            stdout,stderr=(buffers[k].decode('utf-8','replace') for k in ('stdout','stderr'))
            if p.returncode != 0:
                return dict(status='infrastructure_error', stdout=stdout[:65536], stderr=stderr[:65536],
                            returncode=p.returncode, wall_seconds=time.monotonic() - start)
            result = json.loads(stdout)
            result.update(wall_seconds=time.monotonic() - start, image_id=image_id)
            return result
        except subprocess.TimeoutExpired:
            return dict(status='resource_limit', stdout='', stderr='Container wall timeout',
                        returncode=None, wall_seconds=time.monotonic() - start, image_id=image_id)
        except (OSError, ValueError) as e:
            raise SandboxUnavailable(str(e)) from e
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10)
