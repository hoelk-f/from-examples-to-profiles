import ast, json, hashlib, subprocess, time, uuid
from pathlib import Path
from pbe.io import repository
from pbe.runtime_images import resolve_image
ROOT = repository()/"runtimes/legacy"
def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def docker_cmd(cfg, folder, name):
    return ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--read-only', '--memory', '512m', '--cpus', '2', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--user', '65534:65534', '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--workdir', '/tmp', '--mount', f'type=bind,source={folder.resolve()},target=/case,readonly', '--mount', f"type=bind,source={(ROOT / 'python_replay.py').resolve()},target=/replay.py,readonly", '--entrypoint', 'python', resolve_image(ROOT.parent.parent, cfg['images']['python']), '-I', '-B', '/replay.py']


def execute_container(cmd, name, timeout, logdir, prefix):
    start = time.monotonic()
    stdout = logdir / (prefix + '.stdout.txt')
    stderr = logdir / (prefix + '.stderr.txt')
    with stdout.open('wb') as out, stderr.open('wb') as err:
        proc = subprocess.Popen(cmd, stdout=out, stderr=err)
        try:
            rc = proc.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
            proc.kill()
            proc.wait(timeout=10)
            rc, timed_out = (None, True)
        except BaseException:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
            proc.wait(timeout=20)
            raise
    result = {'returncode': rc, 'timed_out': timed_out, 'elapsed_seconds': round(time.monotonic() - start, 3), 'argv': cmd, 'stdout_file': stdout.name, 'stderr_file': stderr.name}
    save(logdir / (prefix + '.json'), result)
    if rc == 125:
        raise RuntimeError('Docker infrastructure failure: ' + stderr.read_text(encoding='utf-8', errors='replace')[:1000])
    return (result, stdout.read_text(encoding='utf-8', errors='replace'))

def direct(cfg, folder, answer, examples):
    record = {'status': 'invalid_python', 'frozen': False}
    try:
        parsed = ast.parse(answer)
    except (SyntaxError, ValueError):
        return record
    if not any((isinstance(n, ast.FunctionDef) and n.name == 'transform' for n in parsed.body)):
        return {'status': 'missing_transform', 'frozen': False}
    case = folder / 'execution'
    case.mkdir()
    (case / 'candidate.py').write_text(answer, encoding='utf-8')
    save(case / 'inputs.json', [e['input'] for e in examples])
    expected = [e['output'] for e in examples]
    checks = []
    for replay in range(2):
        name = 'pbe-sol-py-' + uuid.uuid4().hex[:16]
        outcome, text = execute_container(docker_cmd(cfg, case, name), name, cfg['training_replay_timeout_seconds'], folder, f'replay_{replay}')
        if outcome['timed_out'] or outcome['returncode'] != 0:
            return {'status': 'training_execution_error', 'frozen': False, 'checks': checks + [outcome]}
        response = json.loads(text)
        outputs = [x.get('output') if x.get('status') == 'returned' else None for x in response['results']]
        checks.append({'outputs': outputs, 'expected': expected, 'pass': outputs == expected})
        if outputs != expected:
            return {'status': 'training_mismatch', 'frozen': False, 'checks': checks}
    data = answer.encode('utf-8')
    (folder / 'program.py').write_bytes(data)
    record.update(status='frozen', frozen=True, program_file='program.py', program_sha256=digest(data), checks=checks, runtime='Pinned Python 3.13 Docker interpreter, separate process per replay')
    return record
