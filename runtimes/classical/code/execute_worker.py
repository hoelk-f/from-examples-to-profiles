"""Execute one frozen expression on one input. No synthesis or reference outputs."""
import json
import re
import subprocess
import sys
from pathlib import Path


def synth_literal(s):
    return 'e"' + ''.join(('\\' + c if c in '\\"' else c if 32 <= ord(c) < 127
                           else '\\u{' + format(ord(c), 'x') + '}') for c in s) + '"'


def smt_literal(s):
    return '"' + ''.join('""' if c == '"' else '\\u{' + format(ord(c), 'x') + '}'
                         if c == '\\' or ord(c) < 32 or ord(c) > 126 else c for c in s) + '"'


def rust_string(text):
    if not text.startswith('e"') or not text.endswith('"'):
        raise ValueError('Not a Rust debug string')
    body, out, i = text[2:-1], [], 0
    escapes = {'n': '\n', 'r': '\r', 't': '\t', '0': '\0', '\\': '\\', '"': '"', "'": "'"}
    while i < len(body):
        if body[i] != '\\':
            out.append(body[i]); i += 1; continue
        i += 1
        if i >= len(body):
            raise ValueError('Truncated escape')
        if body[i] in escapes:
            out.append(escapes[body[i]]); i += 1
        elif body.startswith('u{', i):
            end = body.index('}', i + 2)
            out.append(chr(int(body[i + 2:end], 16))); i = end + 1
        else:
            raise ValueError('Unknown Rust escape')
    return ''.join(out)


def smt_string(text):
    text = text.strip()
    if not text.startswith('"'):
        raise ValueError('Expected a ground SMT string, got ' + text[:200])
    out, i = [], 1
    while i < len(text):
        if text[i] == '"':
            if i + 1 < len(text) and text[i + 1] == '"':
                out.append('"'); i += 2; continue
            if text[i + 1:].strip():
                raise ValueError('Trailing SMT output')
            return ''.join(out)
        if text.startswith('\\u{', i):
            end = text.index('}', i + 3)
            out.append(chr(int(text[i + 3:end], 16))); i = end + 1
        elif re.match(r'\\u[0-9a-fA-F]{4}', text[i:]):
            out.append(chr(int(text[i + 2:i + 6], 16))); i += 6
        else:
            out.append(text[i]); i += 1
    raise ValueError('Unclosed SMT string')


def main():
    system = sys.argv[1]
    if system == 'S06':
        sys.path.insert(0, '/adapter')
        from crossbeam_adapter import native_run
    print(json.dumps({'event': 'ready', 'system': system, 'model_loaded': False}), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        response = {'task_id': request['task_id'], 'input_echo': request['input']}
        try:
            if system == 'S06':
                try:
                    output = native_run(request['program']['expression'], request['input'])
                    response.update(status='returned', output=output)
                except Exception as error:
                    response.update(status='execution_error', error_type=type(error).__name__, message=str(error))
            else:
                value = request['input']
                if system == 'S01':
                    script = '(set-logic SLIA)\n' + request['program'] + '\n(assert (= (f ' + synth_literal(value) + ') e""))\n(check-sat)\n'
                    command = ['/opt/synthphonia/target/release/synthphonia', '--emit-values', '/tmp/input.smt2']
                elif system == 'S02':
                    script = '(set-logic QF_SLIA)\n' + request['program'] + '\n(simplify (f ' + smt_literal(value) + '))\n'
                    command = ['/usr/local/bin/cvc5', '--lang=smt2', '/tmp/input.smt2']
                else:
                    raise ValueError('Unknown system')
                Path('/tmp/input.smt2').write_bytes(script.encode('utf-8'))
                process = subprocess.run(command, capture_output=True)
                stdout, stderr = process.stdout.decode('utf-8'), process.stderr.decode('utf-8', errors='replace')
                response.update(native_returncode=process.returncode, native_stdout=stdout, native_stderr=stderr)
                if process.returncode:
                    if system == 'S01' and 'panicked' in stderr and not ('parse(' in stderr or 'ParseError' in stderr):
                        response.update(status='execution_error', error_type='native_panic', message=stderr)
                    else:
                        response.update(status='integration_error', message='Native process failed')
                elif system == 'S01':
                    rows = [s for s in stdout.splitlines() if s.startswith('PBE_OUTPUT ')]
                    if stdout.splitlines().count('PBE_UNDEFINED') == 1 and not rows:
                        response.update(status='execution_error', error_type='native_undefined')
                    else:
                        if len(rows) != 1:
                            raise ValueError('Expected exactly one emitted value')
                        response.update(status='returned', output=rust_string(rows[0][len('PBE_OUTPUT '):]))
                else:
                    response.update(status='returned', output=smt_string(stdout))
        except Exception as error:
            response.update(status='integration_error', error_type=type(error).__name__, message=str(error))
        print(json.dumps(response, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
