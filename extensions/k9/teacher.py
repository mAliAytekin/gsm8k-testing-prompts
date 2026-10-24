import time
from gsm8k_lab.common import ROOT, digest, environment, now, read_json, write_json
from gsm8k_lab.data import GSM8K
from gsm8k_lab.ollama import Ollama
from .core import settings, validate_examples, extension_hashes, training_questions


def prepare():
    config = settings()
    output = ROOT/config['demonstrations']
    if output.exists():
        artifact = read_json(output)
        validate_examples(artifact, config)
        print('Existing teacher examples preserved: '+str(output), flush=True)
        return artifact
    client = Ollama(timeout=config['teacher_timeout_seconds'])
    name = config['teacher_model']
    tag = next((t for t in client.tags() if t['name']==name), None)
    if tag is None:
        raise ValueError('Exact requested teacher is not installed: '+name)
    teacher = dict(name=name, digest=tag['digest'], tag=tag, show=client.show(name),
                   source='Existing local Ollama tag; no substitute or download')
    train = training_questions()
    instruction = (ROOT/'prompts/k9/teacher.txt').read_text().strip()
    context = dict(config=config, teacher=teacher, instruction=instruction,
                   extension_hashes=extension_hashes())
    existing=[]
    for path in (ROOT/'artifacts/k9-teacher').glob('*/metadata.json'):
        saved=read_json(path)
        if saved['config']==config and saved['instruction']==instruction and saved['teacher']['digest']==teacher['digest'] and saved['teacher']['name']==name:
            existing.append(path.parent)
    if len(existing)>1:raise ValueError('Ambiguous matching teacher journals')
    journal = existing[0] if existing else ROOT/'artifacts/k9-teacher'/digest(context)[:20]
    if not existing:
        write_json(journal/'metadata.json', dict(**context, environment=environment(),
                   ollama_version=client.request('/api/version'), created_at=now()))
    examples=[]; records=[]
    for index in config['demonstration_train_indices']:
        q = train[f'gsm8k:train:{index:05d}']
        path = journal/f'{index:05d}.json'
        if path.exists():
            record = read_json(path)
            if record['state'] != 'generated':
                raise RuntimeError('Interrupted teacher request; will not silently regenerate: '+str(path))
        else:
            request = dict(model=name, messages=[{'role':'system','content':instruction},
                           {'role':'user','content':q.text}], stream=False,
                           options=config['teacher_options'], think=config['teacher_think'], keep_alive='10m')
            record = dict(state='inflight', question_id=q.id, question_hash=q.sha256,
                          request=request, started_at=now())
            write_json(path, record)
            print('Teacher generation: '+q.id, flush=True)
            start=time.monotonic()
            response = client.request('/api/chat', request)
            record.update(state='generated', response=response, wall_seconds=time.monotonic()-start)
            write_json(path, record)
        response=record['response']
        if not response.get('done') or response.get('done_reason')=='length' or response.get('eval_count',0)>=config['teacher_options']['num_predict']:
            raise ValueError('Teacher incomplete/truncated; raw response preserved')
        solution=response['message']['content'].strip()
        examples.append(dict(question_id=q.id, question=q.text, question_hash=q.sha256,
                             solution=solution, provenance_file=str(path.relative_to(ROOT)),
                             response_sha256=digest(response),word_count=len(solution.split()),
                             requested_word_limit_compliant=len(solution.split())<=45))
        records.append(record)
        print(solution, flush=True)
    artifact=dict(protocol='k9-v1', teacher=teacher, teacher_options=config['teacher_options'],
                  teacher_think=config['teacher_think'], examples=examples, created_at=now(),
                  preparation_wall_seconds=sum(r['wall_seconds'] for r in records),
                  input_tokens=sum(r['response'].get('prompt_eval_count',0) for r in records),
                  output_tokens=sum(r['response'].get('eval_count',0) for r in records),
                  step_review={'passed':False}, metadata_file=str((journal/'metadata.json').relative_to(ROOT)))
    validate_examples(artifact,config)
    write_json(output,artifact)
    # Explicit model unload is not another solution generation.
    write_json(journal/'unload.json',client.request('/api/generate',{'model':name,'keep_alive':0}))
    print('Teacher answers verified; independent step review required: '+str(output),flush=True)
    return artifact
