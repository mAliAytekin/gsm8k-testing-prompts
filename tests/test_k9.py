import copy
import pytest
from extensions.k9.core import messages,validate_examples,input_upper_bound,training_questions
from gsm8k_lab.common import ROOT,read_json
from gsm8k_lab.data import GSM8K,Question
from gsm8k_lab.prompts import CONDITIONS,messages as original_messages


@pytest.fixture
def examples():
    original=read_json(ROOT/'demonstrations/sets.json')['pairs']
    train=training_questions()
    result=[]
    for d in original['A']+original['B']:
        q=train[f'gsm8k:train:{d["train_index"]:05d}']
        result.append(dict(question_id=q.id,question=q.text,question_hash=q.sha256,solution=d['solutions']['K2']))
    return result


def test_teacher_example_selection_and_gold_validation(examples):
    assert len(validate_examples({'examples':examples}))==4
    broken=copy.deepcopy(examples);broken[0]['solution']='FINAL: 999999'
    with pytest.raises(ValueError):validate_examples({'examples':broken})


def test_same_cot_contract_and_nested_example_questions(examples):
    q=GSM8K().questions('pilot')[0]
    prompt=messages(q,examples)
    original=original_messages(q,next(c for c in CONDITIONS if c.id=='K2_2shot'))  # K2 two-shot
    assert prompt[0]==original[0]
    assert [m['content'] for m in prompt[1:5] if m['role']=='user']==[m['content'] for m in original[1:5] if m['role']=='user']
    assert len(prompt)==10 and prompt[-1]=={'role':'user','content':q.text}


def test_no_target_gold_channel_and_no_demo_overlap(examples):
    q=Question('gsm8k:train:99999','Unique held-out question?', 'hash')
    p=messages(q,examples)
    assert p[-1]['content']==q.text and all(set(m)=={'role','content'} for m in p)
    with pytest.raises(TypeError):messages({'question':q.text,'gold':'SECRET'},examples)
    with pytest.raises(ValueError):messages(Question(examples[0]['question_id'],'x','x'),examples)


def test_context_bound_keeps_output_reservation(examples):
    # A long target cannot pass by ignoring output reservation.
    p=messages(Question('new','x'*4096,'hash'),examples)
    assert input_upper_bound(p)+512>4096


def test_train_jsonl_preserves_embedded_unicode_line_separators():
    questions=training_questions()
    assert len(questions)==7473
    assert '\u2028' in questions['gsm8k:train:02381'].text
