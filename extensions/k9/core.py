import json
from gsm8k_lab.common import ROOT, digest, file_hash, read_json
from gsm8k_lab.data import Question, validate_integrity
from gsm8k_lab.parsing import answer_field, numeric

CONFIG = ROOT / 'configs/k9.json'


def settings():
    return read_json(CONFIG)


def training_questions():
    # JSONL boundaries are physical newlines. str.splitlines() also splits
    # embedded U+2028/U+2029 inside valid question strings in the full train set.
    with (ROOT/'data/train.questions.jsonl').open() as handle:
        return {q.id:q for q in (Question(**json.loads(line)) for line in handle)}


def extension_hashes():
    paths = list((ROOT/'extensions/k9').glob('*.py'))
    paths += [ROOT/'scripts/k9.py', CONFIG, ROOT/'docs/K9_PROTOCOL.md',
              ROOT/'prompts/k9/teacher.txt']
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def validate_examples(artifact, config=None):
    config = config or settings()
    manifest = validate_integrity()
    expected = [f'gsm8k:train:{i:05d}' for i in config['demonstration_train_indices']]
    examples = artifact['examples']
    if [d['question_id'] for d in examples] != expected:
        raise ValueError('Unexpected example IDs/order')
    excluded = set(manifest['ids']['pilot']) | set(manifest['ids']['test'])
    train = training_questions()
    gold = read_json(ROOT/'data/gold.json')
    for d in examples:
        q = train[d['question_id']]
        if q.id in excluded or d['question'] != q.text or d['question_hash'] != q.sha256:
            raise ValueError('Example leakage or modified question')
        if answer_field(d['solution']) != numeric(gold[q.id]):
            raise ValueError('Incorrect teacher example answer')
    return examples


def load_examples():
    config = settings()
    artifact = read_json(ROOT/config['demonstrations'])
    examples = validate_examples(artifact, config)
    review = artifact.get('step_review', {})
    if review.get('passed') is not True or review.get('examples_sha256') != digest(examples):
        raise ValueError('Teacher steps require a hash-bound independent review')
    if artifact['teacher']['name'] != config['teacher_model']:
        raise ValueError('Teacher model changed')
    if artifact['teacher_options'] != config['teacher_options'] or artifact['teacher_think'] != config['teacher_think']:
        raise ValueError('Teacher settings changed')
    for d in examples:
        saved = read_json(ROOT/d['provenance_file'])['response']
        if digest(saved) != d['response_sha256'] or saved['message']['content'].strip() != d['solution']:
            raise ValueError('Teacher response modified after generation')
    return artifact


def messages(question, examples):
    if not isinstance(question, Question):
        raise TypeError('Only Question objects enter evaluation prompts')
    if question.id in {d['question_id'] for d in examples}:
        raise ValueError('Demonstration leakage')
    system = (ROOT/'prompts/v1/common.txt').read_text().strip()+'\n\n'+(ROOT/'prompts/v1/K2.txt').read_text().strip()
    result = [{'role':'system','content':system}]
    for d in examples:
        result += [{'role':'user','content':d['question']},
                   {'role':'assistant','content':d['solution']}]
    return result + [{'role':'user','content':question.text}]


def input_upper_bound(prompt):
    # Identical to the original runner's deliberately conservative preflight.
    return sum(len(m['content'].encode())+64 for m in prompt)+256
