import json
import time
import urllib.error
import urllib.parse
import urllib.request


class InfrastructureError(RuntimeError):
    pass


class Ollama:
    def __init__(self, url='http://127.0.0.1:11434', timeout=180, retries=1):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('Only loopback Ollama endpoints are permitted')
        self.url, self.timeout, self.retries = url.rstrip('/'), timeout, retries

    def request(self, endpoint, payload=None, retry=False):
        for attempt in range((self.retries if retry else 0) + 1):
            req = urllib.request.Request(self.url + endpoint,
                                         None if payload is None else json.dumps(payload).encode(),
                                         {'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.load(response)
                return result
            except urllib.error.HTTPError as e:
                message = e.read(4096).decode(errors='replace')
                # Never regenerate a response to improve model quality.
                raise InfrastructureError(f'HTTP {e.code}: {message}') from e
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                if attempt >= (self.retries if retry else 0):
                    raise InfrastructureError(str(e)) from e
                time.sleep(1)
        raise AssertionError('Unreachable')

    def tags(self):
        return self.request('/api/tags')['models']

    def show(self, name):
        return self.request('/api/show', {'model': name})

    def loaded(self):
        return {m['name'] for m in self.request('/api/ps')['models']}

    def generate(self, name, messages, config, qwen=False):
        payload = dict(model=name, messages=messages, stream=False,
                       options=config['options'], keep_alive=config['keep_alive'])
        if qwen: payload['think'] = False
        # No retry of ambiguous timeouts after a generation was submitted.
        # Retrying is reserved for health/read requests, preserving one sample.
        response = self.request('/api/chat', payload)
        if not response.get('done') or 'message' not in response:
            raise InfrastructureError('Incomplete Ollama response')
        return response, payload
