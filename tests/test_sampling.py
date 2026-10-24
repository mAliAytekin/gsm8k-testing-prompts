from extensions.sampling import all_questions,select
from extensions.repeat10 import settings,ALL,examples,prompts
from extensions.k9.core import input_upper_bound
from gsm8k_lab.common import ROOT,read_json


def test_thousand_sample_fixed_unique_and_answer_blind():
    cfg,base=settings('configs/sample1000.json')
    qs=select(cfg);again=select(cfg)
    assert qs==again and len(qs)==1000 and len({q.id for q in qs})==1000
    assert not {q.id for q in qs}&{'gsm8k:train:00000','gsm8k:train:00002'}
    assert all(set(q.__dict__)=={'id','text','sha256'} for q in qs)
    manifest=read_json(ROOT/cfg['question_manifest'])
    assert manifest['counts']=={'train':858,'test':142}
    demos,_=examples()
    assert max(input_upper_bound(prompts(q,c,demos))+base['options']['num_predict'] for q in qs for c in ALL)<=base['options']['num_ctx']


def test_combined_reader_preserves_unicode_physical_lines():
    qs=all_questions()
    assert len(qs)==8792
    assert '\u2028' in next(q.text for q in qs if q.id=='gsm8k:train:02381')
