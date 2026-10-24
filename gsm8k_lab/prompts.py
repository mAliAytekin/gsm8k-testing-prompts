from dataclasses import dataclass
from .common import ROOT, read_json, digest
from .data import Question

@dataclass(frozen=True)
class Condition:
    id: str
    arm: str
    shots: int

MAIN = [Condition(f'K{i}', f'K{i}', 0) for i in range(2, 7)] + [Condition('K7', 'K6', 1), Condition('K8', 'K6', 2)]
CONTROLS = [Condition(f'K{i}_{s}shot', f'K{i}', s) for i in range(2, 6) for s in (1, 2)]
CONDITIONS = MAIN + CONTROLS

def messages(question: Question, condition: Condition, pair='A'):
    if not isinstance(question, Question): raise TypeError('Question only, no raw dataset rows')
    base = ROOT / 'prompts/v1'
    system = (base / 'common.txt').read_text().strip() + '\n\n' + (base / f'{condition.arm}.txt').read_text().strip()
    result = [{'role':'system','content':system}]
    examples = read_json(ROOT / 'demonstrations/sets.json')['pairs'][pair]
    for d in examples[:condition.shots]:
        if question.id == f"gsm8k:train:{d['train_index']:05d}": raise ValueError('Demonstration leakage')
        result.extend([{'role':'user','content':d['question']}, {'role':'assistant','content':d['solutions'][condition.arm]}])
    result.append({'role':'user','content':question.text})
    return result
