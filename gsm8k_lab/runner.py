import fcntl
import random
import time
from .common import ROOT, digest, environment, file_hash, now, read_json, source_hashes, write_json
from .data import GSM8K, validate_integrity
from .evaluation import evaluate
from .ollama import Ollama, InfrastructureError
from .prompts import CONDITIONS, MAIN, CONTROLS, messages
from .sandbox import Sandbox, SandboxUnavailable
from .store import Store


def make_client(config):
    return Ollama(config['ollama_url'], config['request_timeout_seconds'], config['transport_retries'])


def run(config, phase, model_ids=None, group='all', pair=None, limit=None, generate_only=False, resume_id=None):
    if config.get('qwen_think') is not False: raise ValueError('Qwen thinking must be off')
    if phase == 'main' and limit: raise ValueError('Main evaluation must include all test questions')
    split_manifest = validate_integrity()
    adapter = GSM8K()
    split = 'test' if phase in ('main', 'robustness') else 'pilot'
    questions = adapter.questions(split)
    if phase == 'smoke': questions = questions[:limit or 2]
    elif limit: questions = questions[:limit]
    conditions = {'all': CONDITIONS, 'main': MAIN, 'controls': CONTROLS, 'fewshot': [c for c in CONDITIONS if c.shots]}[group]
    pair = pair or config['demo_pair']
    if phase == 'robustness':
        if pair == 'A' or group != 'fewshot': raise ValueError('Robustness requires pair B/C and group fewshot (10 conditions)')
    elif pair != 'A': raise ValueError('Primary/smoke/pilot pair is pre-fixed to A')
    if phase == 'pilot' and len(questions) != 200: raise ValueError('Pilot requires exactly 200 questions; use smoke for subsets')
    model_ids = model_ids or config['models']
    manifest = read_json(ROOT / 'configs/models.json')
    models = [next(m for m in manifest['models'] if m['id'] == mid) for mid in model_ids]
    client = make_client(config)
    tags = {m['name']: m for m in client.tags()}
    snapshots = {}
    for m in models:
        if m['ollama'] not in tags: raise ValueError('Target missing: ' + m['ollama'])
        show = client.show(m['ollama'])
        if show['details']['quantization_level'] != m['quantization']: raise ValueError('Quantization mismatch')
        snapshots[m['id']] = dict(manifest=m, digest=tags[m['ollama']]['digest'], show=show)
    sandbox = None
    sandbox_info = {'status': 'generation_only'}
    if not generate_only:
        sandbox = Sandbox(config['sandbox_image'], config['sandbox_wall_seconds'])
        try: sandbox_info = sandbox.inspect()
        except SandboxUnavailable as e:
            sandbox_info = {'status': 'unavailable', 'error': str(e)}
            sandbox = None
    identity = dict(config=config, phase=phase, models=snapshots, conditions=[c.__dict__ for c in conditions],
                    question_ids=[q.id for q in questions], split_manifest_hash=digest(split_manifest),
                    demonstration_pair=pair, hashes=source_hashes(), sandbox=sandbox_info, generate_only=generate_only)
    run_id = digest(identity)[:20]
    db_path = ROOT / config['database']
    db_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(str(db_path) + '.lock', 'w')
    try: fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('Another runner owns this database')
    store = Store(db_path)
    if resume_id and resume_id != run_id:
        raise ValueError(f'Resume identity changed: expected {resume_id}, current {run_id}; restore original source/config/environment')
    if phase in ('main', 'robustness'):
        frozen = read_json(ROOT / 'configs/frozen-protocol.json')
        if frozen['config_hash'] != digest(config) or frozen['hashes'] != source_hashes():
            raise ValueError('Protocol is not frozen for these exact sources and config')
        if frozen['model_digests'] != {k: v['digest'] for k, v in snapshots.items()}:
            raise ValueError('Model digest differs from frozen pilot')
        if frozen['sandbox'] != sandbox_info:
            raise ValueError('Sandbox image differs from frozen pilot')
    metadata = dict(id=run_id, identity=identity, environment=environment(), ollama_version=client.request('/api/version'),
                    created_at=now(), expected=len(questions) * len(models) * len(conditions), phase=phase)
    store.add_run(run_id, metadata)
    metadata = store.metadata(run_id)
    write_json(ROOT / f'artifacts/{phase}-latest.json', {'run_id': run_id, 'expected': metadata['expected'], 'database':config['database']})
    print(f'RUN {run_id} phase={phase} expected={metadata["expected"]}', flush=True)
    store.recover(run_id)
    gold = read_json(ROOT / 'data/gold.json')
    for state, record in store.records(run_id):
        if state == 'generated':
            evaluated = evaluate(record, gold[record['question_id']], sandbox)
            store.save(evaluated, 'complete')
    count = len(store.records(run_id))
    # Model blocks minimize load churn; condition order is seeded within question.
    for model in models:
        for question in questions:
            ordered = list(conditions)
            random.Random(config['seed'] + int(question.id.rsplit(':', 1)[1])).shuffle(ordered)
            for condition in ordered:
                prompt = messages(question, condition, pair)
                record = dict(run_id=run_id, config_id=digest(config), question_id=question.id,
                              question_hash=question.sha256, model_id=model['id'], model_digest=snapshots[model['id']]['digest'],
                              condition_id=condition.id, arm=condition.arm, shots=condition.shots,
                              demo_pair=pair if condition.shots else 'none', prompt=prompt, prompt_hash=digest(prompt),
                              created_at=now(), raw_output=None, thinking=None, parsed_output=None, prediction=None,
                              gold=None, error=None, correct=None, status=None, execution=None,
                              generation_wall_seconds=0, load_seconds=0, prompt_seconds=0, decode_seconds=0,
                              input_tokens=None, output_tokens=None, execution_seconds=0, truncated=False,
                              context_overflow=False, context_observability='conservative preflight + server counts; silent server truncation not fully observable')
                if not store.claim(record): continue
                # A conservative UTF-8-byte bound avoids context overflow without inspecting gold.
                # Includes a generous template overhead and reserved generation space.
                upper = sum(len(m['content'].encode()) + 64 for m in prompt) + 256
                if upper + config['options']['num_predict'] > config['options']['num_ctx']:
                    record.update(status='context_overflow', context_overflow=True, error='Conservative input upper bound exceeds context')
                    store.save(evaluate(record, gold[question.id], sandbox), 'complete')
                    count += 1
                    continue
                start = time.monotonic()
                try:
                    record['cold_state'] = 'warm' if model['ollama'] in client.loaded() else 'cold'
                    response, request = client.generate(model['ollama'], prompt, config, qwen=model['id'].startswith('qwen3'))
                    record.update(raw_response=response, request=request, raw_output=response['message']['content'],
                                  thinking=response['message'].get('thinking'), generation_wall_seconds=time.monotonic()-start,
                                  load_seconds=response.get('load_duration', 0)/1e9,
                                  prompt_seconds=response.get('prompt_eval_duration', 0)/1e9,
                                  decode_seconds=response.get('eval_duration', 0)/1e9,
                                  input_tokens=response.get('prompt_eval_count'), output_tokens=response.get('eval_count'),
                                  prompt_cached_tokens=response.get('prompt_eval_cached_count'),
                                  truncated=response.get('done_reason') == 'length' or response.get('eval_count', 0) >= config['options']['num_predict'])
                    if record['thinking']:
                        record.update(status='infrastructure_error', error='Unexpected thinking with think=false')
                    if (record['input_tokens'] or 0) + (record['output_tokens'] or 0) >= config['options']['num_ctx']:
                        record.update(status='context_overflow', context_overflow=True)
                    store.save(record, 'generated')
                    record = evaluate(record, gold[question.id], sandbox)
                except InfrastructureError as e:
                    record.update(status='infrastructure_error', error=str(e), gold=gold[question.id], generation_wall_seconds=time.monotonic()-start)
                store.save(record, 'complete')
                count += 1
                if phase == 'smoke' or count % 50 == 0:
                    print(f'{count}/{metadata["expected"]} {model["id"]} {question.id} {condition.id} {record["status"]}', flush=True)
    write_json(ROOT / f'artifacts/{phase}-completion.json', dict(run_id=run_id, recorded=len(store.records(run_id)), expected=metadata['expected'], ended_at=now()))
    print('FINISHED ' + run_id, flush=True)
    lock_file.close()
    return run_id


def execute_pending(config, run_id):
    store = Store(ROOT / config['database'])
    box = Sandbox(config['sandbox_image'], config['sandbox_wall_seconds'])
    box.inspect()
    gold = read_json(ROOT / 'data/gold.json')
    for state, record in store.records(run_id):
        if state == 'generated' or record.get('status') == 'execution_unavailable':
            result = evaluate(record, gold[record['question_id']], box)
            result['deferred_execution'] = True
            store.save(result, 'complete')
