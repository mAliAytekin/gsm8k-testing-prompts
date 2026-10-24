from gsm8k_lab.store import Store

def record():
    return dict(run_id='synthetic-unit-run',question_id='synthetic-q',model_id='synthetic-m',condition_id='K2',demo_pair='none')

def test_resume_and_duplicate_prevention(tmp_path):
    path=tmp_path/'unit.sqlite';s=Store(path);r=record()
    assert s.claim(r)
    assert not s.claim(r)
    s.save({**r,'raw_output':'2'},'generated')
    again=Store(path);again.recover(r['run_id'])
    assert again.records(r['run_id'])[0][0]=='generated'
    assert not again.claim(r)
    again.save({**r,'status':'correct'},'complete')
    assert len(again.records(r['run_id']))==1

def test_ambiguous_interruption_not_resampled(tmp_path):
    s=Store(tmp_path/'unit.sqlite');r=record();s.claim(r);s.recover(r['run_id'])
    state,got=s.records(r['run_id'])[0]
    assert state=='complete' and got['status']=='infrastructure_error'
    assert got['correct'] is None and not s.claim(r)
