import dataclasses
import pytest
from gsm8k_lab.common import ROOT,read_json
from gsm8k_lab.data import GSM8K,Question,validate_integrity
from gsm8k_lab.prompts import CONDITIONS,messages

def test_split_and_demonstration_separation():
    manifest=validate_integrity()
    pilot=GSM8K().questions('pilot');test=GSM8K().questions('test')
    assert len(pilot)==200 and len(test)==1319
    demos={f'gsm8k:train:{i:05d}' for i in manifest['demonstration_indices']}
    assert not ({q.id for q in pilot}&demos)
    assert not ({q.id for q in pilot}&{q.id for q in test})

def test_prompt_has_no_evaluation_gold_channel():
    q=Question('gsm8k:train:99999','A unique held-out question?', 'hash')
    assert {f.name for f in dataclasses.fields(Question)}=={'id','text','sha256'}
    for c in CONDITIONS:
        m=messages(q,c)
        assert m[-1]=={'role':'user','content':q.text}
        assert len(m)==2+2*c.shots
        assert all('answer' not in x and 'gold' not in x for x in m)
    with pytest.raises(TypeError):messages({'question':'q','answer':'SECRET_GOLD'},CONDITIONS[0])

def test_demo_leakage_rejected():
    with pytest.raises(ValueError):messages(Question('gsm8k:train:00000','x','h'),next(c for c in CONDITIONS if c.id=='K7'))

def test_sympy_instructions_identical_and_nested_examples():
    q=GSM8K().questions('pilot')[0]
    k6,k7,k8=[messages(q,c) for c in CONDITIONS if c.id in ('K6','K7','K8')]
    assert k6[0]==k7[0]==k8[0]
    assert k7[1:3]==k8[1:3]
    for pair in ['A','B','C']:
        for shots in [1,2]:
            question_lists=[[m['content'] for m in messages(q,c,pair)[1:-1] if m['role']=='user'] for c in CONDITIONS if c.shots==shots]
            assert all(x==question_lists[0] for x in question_lists)
