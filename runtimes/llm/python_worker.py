"""Offline execution-only worker. No expected output is received."""
import contextlib
import io
import json
from pathlib import Path
import sys

source=Path('/candidate/program.py').read_text(encoding='utf-8')
compiled=compile(source,'<frozen-program>','exec')
print(json.dumps({'event':'ready','model_loaded':False}),flush=True)
for line in sys.stdin:
    request=json.loads(line)
    if set(request)!={'id','input'}:
        raise ValueError('Unexpected request fields')
    result={'id':request['id'],'input_echo':request['input']}
    namespace={'__name__':'synthesized_program'}
    try:
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            exec(compiled,namespace)
            answer=namespace['transform'](request['input'])
        if isinstance(answer,str):
            if len(answer)>1000000:
                raise ValueError('Output exceeds protocol limit')
            result.update(status='returned',output=answer)
        else:
            result.update(status='non_string_output',output=None,returned_type=type(answer).__name__)
    except BaseException as exc:
        result.update(status='execution_error',error_type=type(exc).__name__,message=str(exc)[:2000])
    print(json.dumps(result,ensure_ascii=True),flush=True)
