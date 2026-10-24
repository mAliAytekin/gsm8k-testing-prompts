"""Dataset boundary: generation gets Question objects, never gold solutions."""
import csv
import json
import random
import subprocess
from dataclasses import dataclass
from typing import Protocol
from .common import ROOT, digest, file_hash, read_json, write_json
from .parsing import numeric


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    sha256: str


class DatasetAdapter(Protocol):
    def questions(self, split: str) -> list[Question]: ...
    def gold(self, question_id: str) -> str: ...


class GSM8K:
    def __init__(self, root=ROOT / 'data'):
        self.root = root

    def questions(self, split):
        return [Question(**json.loads(line)) for line in (self.root / f'{split}.questions.jsonl').read_text().splitlines()]

    def gold(self, question_id):
        return read_json(self.root / 'gold.json')[question_id]


def prepare():
    root = ROOT / 'data'
    raw = root / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    revision = read_json(ROOT / 'sources/gsm8k_revision.json')['revision']
    all_rows = {}
    hashes = {}
    for split, count in [('train', 7473), ('test', 1319)]:
        path = raw / f'{split}.jsonl'
        if not path.exists():
            subprocess.run(['curl', '-fLsS', '--retry', '3', '-o', str(path),
                            f'https://raw.githubusercontent.com/openai/grade-school-math/{revision}/grade_school_math/data/{split}.jsonl'], check=True)
        hashes[split] = file_hash(path)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len(rows) != count: raise ValueError('Unexpected dataset size')
        all_rows[split] = rows
    if (root / 'split-manifest.json').exists():
        previous = read_json(root / 'split-manifest.json')
        if previous['raw_sha256'] != hashes: raise ValueError('Dataset changed; refusing overwrite')
    pilot = sorted(random.Random(20261021).sample(range(7473), 200))
    demos = read_json(ROOT / 'demonstrations/sets.json')
    demo_ids = {d['train_index'] for pair in demos['pairs'].values() for d in pair}
    if set(pilot) & demo_ids: raise ValueError('Demonstration/pilot leakage')
    gold = {}
    ids = {}
    for split, indices in [('pilot', pilot), ('test', range(1319)), ('train', range(7473))]:
        source = 'test' if split == 'test' else 'train'
        questions = []
        for i in indices:
            row = all_rows[source][i]
            qid = f'gsm8k:{source}:{i:05d}'
            questions.append(dict(id=qid, text=row['question'], sha256=digest(row['question'])))
            gold[qid] = str(numeric(row['answer'].rsplit('####', 1)[1]))
        (root / f'{split}.questions.jsonl').write_text(''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in questions))
        ids[split] = [q['id'] for q in questions]
    for pair in demos['pairs'].values():
        for d in pair:
            row = all_rows['train'][d['train_index']]
            if d['question'] != row['question'] or numeric(d['answer']) != numeric(row['answer'].rsplit('####', 1)[1]):
                raise ValueError('Demonstration does not match official train data')
    write_json(root / 'gold.json', gold)
    manifest = dict(dataset='GSM8K main', revision=revision, seed=20261021, pilot_count=200,
                    raw_sha256=hashes, ids=ids, demonstration_indices=sorted(demo_ids),
                    processed_sha256={p.name: file_hash(p) for p in root.glob('*.questions.jsonl')},
                    gold_sha256=file_hash(root / 'gold.json'))
    write_json(root / 'split-manifest.json', manifest)
    annotation = root / 'annotations-template.csv'
    if not annotation.exists():
        with annotation.open('w') as f:
            w = csv.writer(f)
            w.writerow(['question_id', 'question', 'process_sequence', 'equation_need', 'quantity_structure', 'reviewer', 'validated', 'rationale'])
            for q in GSM8K().questions('pilot') + GSM8K().questions('test'):
                w.writerow([q.id, q.text, '', '', '', '', '', ''])
    return manifest


def validate_integrity():
    m = read_json(ROOT / 'data/split-manifest.json')
    for name, expected in m['processed_sha256'].items():
        if file_hash(ROOT / 'data' / name) != expected: raise ValueError('Question file changed: ' + name)
    if file_hash(ROOT / 'data/gold.json') != m['gold_sha256']: raise ValueError('Gold file changed')
    return m
