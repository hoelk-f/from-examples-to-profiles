from __future__ import annotations
import hashlib, json, pathlib, queue, subprocess, sys, threading, time, uuid
from datetime import datetime, timezone
from pbe.io import repository
from pbe.runtime_images import resolve_image
ROOT = repository() / 'runtimes/classical'
sys.path.insert(0, str(ROOT / 'vendor'))
import run_classical as native_syntax
import run_merlin as merlin_syntax
import merlin_export
CONFIG_BYTES = (ROOT / 'configuration.json').read_bytes()
CONFIG = json.loads(CONFIG_BYTES)
CONFIG_HASH = hashlib.sha256(CONFIG_BYTES).hexdigest()
IMAGES = {s: v['Id'] for s, v in json.loads((ROOT / 'images.json').read_text('utf-8')).items()}
RUNTIME = ROOT.parent / 'sensitivity/build-adapters/prose/runtime'
ADAPTERS = ROOT.parent / 'sensitivity/adapters'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')

def synth_literal(s):
    return 'e"' + ''.join(('\\' + c if c in '\\"' else c if 32 <= ord(c) < 127 else '\\u{' + format(ord(c), 'x') + '}' for c in s)) + '"'

def merlin_literal(s):
    if '"' in s:
        raise ValueError('Merlin raw literal parser cannot encode a double quote')
    return '"' + s + '"'
native_syntax.native_literal = synth_literal
merlin_syntax.native_literal = merlin_literal

def base(system, name, folder):
    return ['docker', 'run', '--name', name, '--network', 'none', '--read-only', '--memory', str(CONFIG['memory_gib']) + 'g', '--memory-swap', str(CONFIG['memory_gib']) + 'g', '--cpus', str(CONFIG['cpus']), '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,exec,size=256m' if system == 'S08' else '/tmp:rw,size=256m', '-e', 'PYTHONHASHSEED=' + CONFIG['pythonhashseed'], '-e', 'PYTHONDONTWRITEBYTECODE=1', '--mount', f"type=bind,source={ADAPTERS},target=/adapter,readonly", '--mount', f'type=bind,source={folder},target=/case,readonly', '-i']

def command(system, name, folder, execute=False):
    cmd = base(system, name, folder)
    image = resolve_image(ROOT.parent.parent, IMAGES[system])
    if system in ['S01', 'S02']:
        if execute:
            entry = '/opt/synthphonia/target/release/synthphonia' if system == 'S01' else '/usr/local/bin/cvc5'
            args = ['--emit-values', '/case/check.smt2'] if system == 'S01' else ['--lang=smt2', '/case/check.smt2']
        else:
            entry = 'python3'
            args = ['-u', '/adapter/native_worker.py', system]
    elif system == 'S03':
        cmd += ['--mount', f'type=bind,source={RUNTIME},target=/prose,readonly']
        entry = 'dotnet'
        args = ['/prose/Qualification.dll']
    elif system == 'S06':
        entry = 'python'
        args = ['-u', '/adapter/crossbeam_execute.py' if execute else '/adapter/crossbeam_adapter.py']
    else:
        cmd += ['--mount', f"type=bind,source={ADAPTERS.parent / 'build-adapters/bustle/classes'},target=/sensitivity-adapter,readonly"]
        return cmd + ['--entrypoint', 'java', image, '-Xmx3g', '-XX:ActiveProcessorCount=2', '-Djava.util.concurrent.ForkJoinPool.common.parallelism=2', '-cp', '/sensitivity-adapter:/opt/bustle/classes:/opt/bustle/lib/*', 'com.googleresearch.bustle.RunAdapter'] + (['execute-only'] if execute else [])
    return cmd + ['--entrypoint', entry, image, *args]

def inspect(name):
    p = subprocess.run(['docker', 'inspect', name, '--format', '{{json .State}}'], capture_output=True, timeout=15)
    return json.loads(p.stdout) if p.returncode == 0 else {'inspection_error': p.stderr.decode(errors='replace')}

class Deadline(Exception):
    pass

class ProcessEnded(Exception):
    pass

class ProtocolError(Exception):
    pass

class Engine:

    def __init__(self, system, folder):
        self.system = system
        self.folder = folder
        self.name = 'pbe-prep-' + uuid.uuid4().hex[:12]
        self.events = queue.Queue()
        self.cmd = command(system, self.name, folder)
        self.err = (folder / 'stderr.log').open('wb')
        self.out = (folder / 'stdout.jsonl').open('wb')
        self.started = time.monotonic()
        self.finished = False
        self.search_submitted = None
        self.process = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err)

        def read():
            try:
                for line in self.process.stdout:
                    observed = time.monotonic()
                    self.out.write(line)
                    self.out.flush()
                    try:
                        obj = json.loads(line)
                    except (ValueError, UnicodeDecodeError):
                        obj = {'event': 'unparsed_output', 'text': line.decode(errors='replace')}
                    self.events.put((observed, obj))
            finally:
                self.events.put((time.monotonic(), None))
        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()

    def receive(self, deadline):
        try:
            observed, obj = self.events.get(timeout=max(0, deadline - time.monotonic()))
        except queue.Empty:
            raise Deadline()
        if observed > deadline:
            raise Deadline()
        if obj is None:
            raise ProcessEnded()
        return (observed, obj)

    def ready(self):
        received, obj = self.receive(self.started + CONFIG['initialization_seconds'])
        if (obj.get('event') or obj.get('event_type')) != 'ready':
            raise ProtocolError('Missing ready event')
        if self.system == 'S06' and obj.get('pythonhashseed') != CONFIG['pythonhashseed']:
            raise ProtocolError('Hashseed was not applied before startup')
        self.ready_at = received
        self.ready_event = obj
        return received - self.started

    def request(self, payload, seconds, export_seconds):
        self.search_submitted = time.monotonic()
        self.process.stdin.write((json.dumps(payload, ensure_ascii=False) + '\n').encode())
        self.process.stdin.flush()
        deadline = self.search_submitted + seconds
        completed = False
        while True:
            observed, obj = self.receive(deadline)
            if obj.get('task_id') != payload['task_id']:
                raise ProtocolError('Task ID mismatch')
            if (obj.get('event') or obj.get('event_type')) == 'search_complete':
                if completed:
                    raise ProtocolError('Repeated search_complete')
                self.search_seconds = observed - self.search_submitted
                completed = True
                deadline = observed + export_seconds
            elif 'status' in obj:
                if not completed and obj['status'] not in ['adapter_error', 'search_timeout']:
                    raise ProtocolError('Result without completed search')
                self.phase = 'export' if completed else 'search'
                self.result_received = observed
                self.export_seconds = observed - (self.search_submitted + self.search_seconds) if completed else 0
                return obj
            else:
                raise ProtocolError('Unexpected protocol event')

    def close(self, kill=False):
        if self.finished:
            return self.state
        self.finished = True
        if kill:
            subprocess.run(['docker', 'kill', self.name], capture_output=True, timeout=15)
        try:
            if self.process.stdin and (not self.process.stdin.closed):
                self.process.stdin.close()
            self.process.wait(timeout=5)
        except (subprocess.TimeoutExpired, BrokenPipeError):
            subprocess.run(['docker', 'kill', self.name], capture_output=True, timeout=15)
            self.process.wait(timeout=15)
        self.reader.join(timeout=5)
        self.state = inspect(self.name)
        subprocess.run(['docker', 'rm', '-f', self.name], capture_output=True, timeout=15)
        self.err.close()
        self.out.close()
        save(self.folder / 'engine.json', {'command': self.cmd, 'state': self.state, 'docker_client_exit_code': self.process.returncode, 'ready': getattr(self, 'ready_event', None)})
        return self.state

def classify_failure(response, state, stderr, fallback):
    if state.get('OOMKilled') or response.get('native_oom_kill_delta', 0) > 0:
        return 'out_of_memory'
    if ('char boundary' in stderr or 'character boundary' in stderr) and 'panicked' in stderr:
        return 'unicode_search_error'
    return fallback

def verify(system, task, program, folder):
    expected = [e['output'] for e in task['examples']]
    inputs = [e['input'] for e in task['examples']]
    if system == 'S01':
        text = '(set-logic SLIA)\n' + program + '\n' + ''.join(('(assert (= (f ' + synth_literal(e['input']) + ') ' + synth_literal(e['output']) + '))\n' for e in task['examples'])) + '(check-sat)\n'
        (folder / 'check.smt2').write_text(text, encoding='utf-8')
        request = None
    elif system == 'S02':
        terms = ' '.join(('(= (f ' + merlin_export.literal(e['input']) + ') ' + merlin_export.literal(e['output']) + ')' for e in task['examples']))
        (folder / 'check.smt2').write_text('(set-logic QF_SLIA)\n' + program + '\n(assert (not (and ' + terms + ')))\n(check-sat)\n', encoding='utf-8')
        request = None
    elif system == 'S03':
        request = {'task_id': task['task_id'], 'operation': 'execute', 'program': program, 'inputs': inputs}
    elif system == 'S06':
        request = {'task_id': task['task_id'], 'expression': program['expression'], 'inputs': inputs}
    else:
        request = {'task_id': task['task_id'], 'ast': program['ast'], 'inputs': inputs}
    name = 'pbe-prep-check-' + uuid.uuid4().hex[:12]
    cmd = command(system, name, folder, True)
    data = None if request is None else (json.dumps(request, ensure_ascii=False) + '\n').encode()
    timed = False
    start = time.monotonic()
    try:
        p = subprocess.run(cmd, input=data, capture_output=True, timeout=CONFIG['verification_seconds'])
        stdout = p.stdout
        stderr = p.stderr
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        timed = True
        stdout = e.stdout or b''
        stderr = e.stderr or b''
        code = None
        subprocess.run(['docker', 'kill', name], capture_output=True, timeout=15)
    state = inspect(name)
    subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=15)
    record = {'command': cmd, 'request': request, 'seconds': time.monotonic() - start, 'stdout': stdout.decode('utf-8', 'replace'), 'stderr': stderr.decode('utf-8', 'replace'), 'returncode': code, 'timeout': timed, 'container_state': state}
    if timed:
        status = 'verification_timeout'
    elif state.get('OOMKilled'):
        status = 'out_of_memory'
    elif code != 0:
        status = 'reload_error'
    elif system == 'S01':
        status = 'frozen' if record['stdout'].strip().splitlines()[-1:] == [str(len(task['examples']))] else 'reload_mismatch'
    elif system == 'S02':
        status = 'frozen' if record['stdout'].strip() == 'unsat' else 'reload_mismatch'
    else:
        rows = [json.loads(line) for line in record['stdout'].splitlines() if line.startswith('{')]
        replies = [r for r in rows if r.get('task_id') == task['task_id']]
        good = len(replies) == 1 and replies[0].get('status') == 'executed' and (replies[0].get('outputs') == expected)
        if system == 'S03':
            good = good and replies[0].get('roundtrip_equal') is True
        if system == 'S08':
            good = good and replies[0].get('ast') == program['ast'] and (rows[0].get('model_loaded') is False)
        status = 'frozen' if good else 'reload_mismatch'
    record['status'] = status
    save(folder / 'reload.json', record)
    return status

def run_one(system, task, folder, control_overrides=None):
    if system not in CONFIG['active_local_systems']:
        raise ValueError('Unprepared system')
    if set(task) != {'task_id', 'examples'} or not 1 <= len(task['examples']) <= 5:
        raise ValueError('An isolated task ID and one to five pairs are required')
    if any((set(e) != {'input', 'output'} or not all((isinstance(v, str) for v in e.values())) for e in task['examples'])):
        raise ValueError('Bad examples')
    folder.mkdir(parents=True, exist_ok=False)
    record = {'schema_version': 1, 'system': system, 'task_id': task['task_id'], 'started_at': datetime.now(timezone.utc).isoformat(), 'frozen': False, 'status': None, 'image_id': IMAGES[system], 'config_sha256': CONFIG_HASH, 'task_payload_sha256': sha(json.dumps(task, sort_keys=True, ensure_ascii=False).encode()), 'training_count': len(task['examples']), 'timings': {}, 'control_overrides': control_overrides}
    save(folder / 'training.json', task)

    def finish(status):
        record['status'] = status
        save(folder / 'result.json', record)
        return record
    try:
        if system in ['S01', 'S02']:
            text = (native_syntax if system == 'S01' else merlin_syntax).sygus(task['examples'])
            (folder / 'task.sl').write_text(text, encoding='utf-8')
    except ValueError as e:
        record['reason'] = str(e)
        return finish('unsupported_transport')
    payload = {**task, 'timeout_seconds': CONFIG['search_seconds'], 'seed': CONFIG['search_seed']}
    if system == 'S06':
        payload['max_values_explored'] = CONFIG['crossbeam']['max_values_explored']
    if system == 'S08':
        payload['max_expressions'] = CONFIG['bustle']['max_expressions']
    if control_overrides:
        if not task['task_id'].startswith('CONTROL-'):
            raise ValueError('Overrides only for independent technical controls')
        payload.update(control_overrides)
    save(folder / 'request.json', payload)
    engine = None
    response = {}
    failure = None
    try:
        engine = Engine(system, folder)
        record['timings']['initialization_seconds'] = engine.ready()
        response = engine.request(payload, payload['timeout_seconds'], CONFIG['export_seconds'])
        record['response'] = response
        record['timings'].update(search_seconds=getattr(engine, 'search_seconds', None), export_seconds=getattr(engine, 'export_seconds', None))
    except Deadline:
        if engine and engine.search_submitted is not None:
            record['timings']['request_until_deadline_seconds'] = time.monotonic() - engine.search_submitted
        failure = 'initialization_timeout' if engine is None or engine.search_submitted is None else 'export_timeout' if hasattr(engine, 'search_seconds') else 'search_timeout'
    except (ProcessEnded, BrokenPipeError):
        failure = 'initialization_error' if engine is None or engine.search_submitted is None else 'process_error'
    except (ProtocolError, ValueError) as e:
        failure = 'protocol_error'
        record['reason'] = str(e)
    except Exception as e:
        failure = 'adapter_error'
        record['reason'] = repr(e)
    finally:
        state = engine.close(kill=failure is not None) if engine is not None else {}
        record['container_state'] = state
        if engine and engine.search_submitted is not None:
            record['timings']['task_wall_until_cleanup_seconds'] = time.monotonic() - engine.search_submitted
    stderr = (folder / 'stderr.log').read_text('utf-8', errors='replace') if (folder / 'stderr.log').exists() else ''
    if failure:
        return finish(classify_failure(response, state, stderr, failure))
    if response.get('status') == 'search_timeout':
        return finish('search_timeout')
    if response.get('status') in ['mismatch', 'training_or_reload_mismatch']:
        return finish('training_mismatch')
    if response.get('status') == 'adapter_error':
        return finish(classify_failure(response, state, stderr, 'adapter_error'))
    if system in ['S01', 'S02'] and response.get('native_exit_code') != 0:
        return finish(classify_failure(response, state, stderr, 'process_error'))
    if response.get('status') in ['no_program', 'no_program_within_budget']:
        if system == 'S08' and response.get('native_result', {}).get('numExpressionsTried', 0) >= payload['max_expressions']:
            return finish('candidate_limit')
        if system == 'S06' and response.get('stats', {}).get('num_values_explored', 0) >= payload['max_values_explored']:
            return finish('candidate_limit')
        return finish('no_program_returned')
    try:
        if system == 'S01':
            raw = response['native_stdout']
            start = raw.find('(define-fun')
            if start < 0:
                return finish('no_program_returned')
            program = native_syntax.sexpr_at(raw, start)
            filename = 'candidate.smt2'
            data = (program + '\n').encode()
        elif system == 'S02':
            program = '(define-fun f ((x String)) String ' + merlin_export.expression(response['native_stdout']) + ')'
            filename = 'candidate.smt2'
            data = (program + '\n').encode()
        else:
            expected = [e['output'] for e in task['examples']]
            if response.get('status') != 'program':
                return finish('protocol_error')
            if response.get('native_outputs') != expected or response.get('restored_outputs') != expected:
                return finish('training_mismatch')
            if system == 'S03':
                program = response['program']
            elif system == 'S06':
                program = {'expression': response['expression'], 'language': 'CrossBeam native BUSTLE DSL'}
            else:
                program = {'ast': response['ast'], 'language': 'BUSTLE original Java DSL'}
            filename = 'candidate.json'
            data = (json.dumps(program, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
        (folder / filename).write_bytes(data)
        record.update(candidate_file=filename, candidate_sha256=sha(data))
    except Exception as e:
        record['reason'] = repr(e)
        return finish('export_error')
    try:
        status = verify(system, task, program, folder)
    except Exception as e:
        record['reason'] = repr(e)
        return finish('reload_error')
    if status == 'frozen':
        record.update(frozen=True, program_file=filename, program_sha256=sha(data))
    return finish(status)
