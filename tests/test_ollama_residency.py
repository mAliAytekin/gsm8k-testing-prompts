import io
import json
import urllib.request
import pytest
from gsm8k_lab.ollama import Ollama, InfrastructureError


def transport(monkeypatch, generation):
    requests = []
    def urlopen(request, timeout):
        body = json.loads(request.data) if request.data else None
        requests.append((request.full_url, body))
        response = generation if body and body.get('messages') else {'done': True}
        return io.BytesIO(json.dumps(response).encode())
    monkeypatch.setattr(urllib.request,'urlopen',urlopen)
    return requests


def test_generation_respects_residency_without_unload(monkeypatch):
    calls = transport(monkeypatch,{'done':True,'message':{'content':'READY'},'prompt_eval_cached_count':0})
    response, request = Ollama().generate('model',[{'role':'user','content':'check'}],
                                         {'options':{},'keep_alive':'30m'})
    assert len(calls)==1
    assert request['keep_alive']==calls[0][1]['keep_alive']=='30m'


def test_direct_teacher_keep_alive_is_preserved(monkeypatch):
    calls = transport(monkeypatch,{'done':True,'message':{'content':'READY'}})
    request = {'model':'teacher','messages':[{'role':'user','content':'check'}],'keep_alive':'10m'}
    Ollama().request('/api/chat',request)
    assert len(calls)==1 and request['keep_alive']=='10m'


def test_cache_reuse_is_returned_without_retry_or_rejection(monkeypatch):
    calls = transport(monkeypatch,{'done':True,'message':{'content':'READY'},'prompt_eval_cached_count':17})
    result=Ollama().request('/api/chat',{'model':'m','messages':[{'role':'user','content':'x'}]})
    assert result['prompt_eval_cached_count']==17 and len(calls)==1
