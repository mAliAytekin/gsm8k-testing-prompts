import pytest
from gsm8k_lab.evaluation import evaluate
from gsm8k_lab.analysis import paired_ci,mcnemar,holm
from gsm8k_lab.sandbox import Sandbox,SandboxUnavailable

def test_execution_fails_closed():
    r=evaluate({'raw_output':'print("FINAL: 2")','arm':'K4'},'2',None)
    assert r['status']=='execution_unavailable' and r['correct'] is None

def test_model_failures_are_not_filtered():
    for record,status in [({'raw_output':'FINAL: 3','arm':'K2'},'wrong_answer'),
                          ({'raw_output':'print(','arm':'K4'},'syntax_error'),
                          ({'raw_output':'FINAL: 2','arm':'K2','truncated':True},'generation_truncated'),
                          ({'raw_output':'2\n3','arm':'K2'},'format_error')]:
        r=evaluate(record,'2');assert r['status']==status and r['correct'] is False

def test_paired_statistics():
    delta,ci=paired_ci([1,1,1,1],[0,0,0,0],1000)
    assert delta==1 and ci==[1,1]
    assert mcnemar([1]*5,[0]*5)['p']==0.0625
    assert holm([.01,.03,.2])==[.03,.06,.2]
    import numpy as np
    assert 0<=mcnemar(np.ones(1319,dtype=int),np.zeros(1319,dtype=int))['p']<=1

def test_nonlocal_ollama_rejected():
    from gsm8k_lab.ollama import Ollama
    with pytest.raises(ValueError):Ollama('http://0.0.0.0:11434')


def test_unknown_representation_cannot_fall_through_to_code_execution():
    class MustNotRun:
        def run(self, code):
            pytest.fail('Unsupported representation reached sandbox')
    with pytest.raises(ValueError, match='Unsupported'):
        evaluate({'raw_output':'print("FINAL: 2")','arm':'unsupported'},'2',MustNotRun())
