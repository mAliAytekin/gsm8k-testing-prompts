import time
from .parsing import FormatError, ResourceError, numeric, answer_field, code_output, extract_code, arithmetic
from .sandbox import SandboxUnavailable


def evaluate(record, gold, sandbox=None):
    if record["arm"] not in {"K2", "K3", "K4", "K5", "K6"}:
        raise ValueError("Unsupported solution representation")
    r = dict(record)
    r.update(gold=gold, prediction=None, parsed_output=None, correct=False, error=None,
             parseable=False, executable=None, executed_code=None, execution=None, execution_seconds=0.0)
    if r.get('status') in ('infrastructure_error', 'context_overflow'):
        r['correct'] = None
        return r
    if r.get('truncated'):
        r.update(status='generation_truncated', error='Ollama length stop or token cap reached')
        return r
    text, arm = r['raw_output'], r['arm']
    try:
        if arm == 'K2':
            prediction = answer_field(text)
            r['parsed_output'] = text.strip().splitlines()[-1]
        elif arm == 'K3':
            start = time.monotonic()
            prediction = arithmetic(text)
            r['execution_seconds'] = time.monotonic() - start
            r.update(parsed_output=text.strip(), executable=True)
        else:
            code = extract_code(text)
            r.update(parsed_output=code, parseable=True, executed_code=code, executable=False)
            if sandbox is None: raise SandboxUnavailable('Generation only: isolated execution pending')
            result = sandbox.run(code)
            r.update(execution=result, execution_seconds=result['wall_seconds'])
            if result['status'] == 'infrastructure_error':
                r.update(status='infrastructure_error', error=result['stderr'], correct=None)
                return r
            if result['status'] == 'resource_limit':
                r.update(status='resource_limit', error=result['stderr'])
                return r
            if result['returncode'] != 0:
                status = 'syntax_error' if 'SyntaxError:' in result['stderr'] else 'runtime_api_error'
                r.update(status=status, error=result['stderr'])
                return r
            r['executable'] = True
            prediction = code_output(result['stdout'])
        r.update(parseable=True, prediction=str(prediction), correct=(prediction == numeric(gold)))
        r['status'] = 'correct' if r['correct'] else 'wrong_answer'
    except SyntaxError as e:
        r.update(status='syntax_error', error=str(e))
    except FormatError as e:
        r.update(status='format_error', error=str(e))
    except (ResourceError, RecursionError, MemoryError) as e:
        r.update(status='resource_limit', error=str(e))
    except (ZeroDivisionError, OverflowError) as e:
        r.update(status='runtime_api_error', error=str(e))
    except SandboxUnavailable as e:
        r.update(status='execution_unavailable', error=str(e), correct=None)
    return r
