import pytest
from gsm8k_lab.data import GSM8K
from gsm8k_lab.common import ROOT,read_json
from extensions.repeat10 import ALL,examples,prompts,settings


def test_repeat16_and_teacher_one_example():
    demos,teacher=examples();cfg,base=settings()
    assert len(ALL)==16 and len({c.id for c in ALL})==16
    assert base['keep_alive']=='30m' and cfg['question_count']==10
    assert len(demos['K9'])==1 and demos['K9'][0]==teacher['examples'][0]
    questions=GSM8K().questions('pilot')[:10]
    for q in questions:
        for c in ALL:
            p=prompts(q,c,demos)
            assert p[-1]=={'role':'user','content':q.text}
            assert len(p)==2+2*c.shots
    assert teacher['teacher']['name']=='gemma4:26b-mlx'


def test_fixed_ids_disjoint_from_demos_and_test():
    manifest=read_json(ROOT/'data/split-manifest.json')
    ids={q.id for q in GSM8K().questions('pilot')[:10]}
    assert len(ids)==10 and ids<=set(manifest['ids']['pilot'])
    assert not ids & set(manifest['ids']['test'])
    assert not ids & {'gsm8k:train:00000','gsm8k:train:00002'}


def test_removed_conditions_not_scheduled():
    from gsm8k_lab.runner import CONDITIONS, MAIN
    assert len(CONDITIONS) == 15 and len(MAIN) == 7
    assert {c.id for c in ALL} == {c.id for c in CONDITIONS} | {'K9'}
    assert not ({'K1', 'K10', 'K1_Formated', 'K1_Formatted'} & {c.id for c in ALL})
