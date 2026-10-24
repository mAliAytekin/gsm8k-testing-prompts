"""Answer-blind fixed sampling from official physical-line question files."""
import json
import random
from gsm8k_lab.common import ROOT,read_json,write_json,digest
from gsm8k_lab.data import GSM8K,Question,validate_integrity


def all_questions():
    return [Question(**json.loads(line)) for split in ('train','test') for line in (ROOT/f'data/{split}.questions.jsonl').open()]


def select(cfg):
    if 'question_manifest' not in cfg:return GSM8K().questions('pilot')[:cfg['question_count']]
    split=validate_integrity();pool=all_questions();assert len(pool)==8792
    pairs=read_json(ROOT/'demonstrations/sets.json')['pairs']
    excluded={f'gsm8k:train:{d["train_index"]:05d}' for d in pairs[cfg['demonstration_pair']]}
    excluded.add(cfg['k9_example_id'])
    eligible=sorted((q for q in pool if q.id not in excluded),key=lambda q:q.id)
    chosen=sorted(random.Random(cfg['selection_seed']).sample(eligible,cfg['question_count']),key=lambda q:q.id)
    manifest=dict(version='sample-v1',seed=cfg['selection_seed'],source_split_hash=digest(split),excluded_ids=sorted(excluded),eligible_count=len(eligible),question_ids=[q.id for q in chosen],question_hashes={q.id:q.sha256 for q in chosen},counts={s:sum(q.id.startswith(f'gsm8k:{s}:') for q in chosen) for s in ('train','test')},previous_pilot_ids=sorted({q.id for q in chosen}&set(split['ids']['pilot'])))
    path=ROOT/cfg['question_manifest']
    if path.exists():
        if read_json(path)!=manifest:raise ValueError('Fixed sample manifest changed')
    else:write_json(path,manifest)
    return chosen
