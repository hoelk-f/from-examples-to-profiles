"""Executed only inside the read-only, offline Python container."""
import contextlib
import io
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
source = Path('/case/candidate.py').read_text(encoding='utf-8')
inputs = json.loads(Path('/case/inputs.json').read_text(encoding='utf-8'))
result = []
for value in inputs:
    # A fresh namespace for each input, as well as a fresh process for each replay.
    namespace = {'__name__': 'synthesized_program'}
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(source, '<candidate>', 'exec'), namespace)
            answer = namespace['transform'](value)
        if not isinstance(answer, str):
            raise TypeError('transform did not return str')
        if len(answer) > 100000:
            raise ValueError('Output exceeds limit')
        result.append({'status': 'returned', 'output': answer})
    except BaseException as exc:
        result.append({'status': 'error', 'type': type(exc).__name__, 'message': str(exc)[:1000]})
sys.stdout.write(json.dumps({'results': result}, ensure_ascii=False) + '\n')
