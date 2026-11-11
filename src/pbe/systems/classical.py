import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def now():
    return datetime.now(timezone.utc).isoformat()

class InfrastructureError(Exception):
    pass

class Deadline(Exception):
    pass

class ProcessEnded(Exception):
    pass

class Engine:

    def __init__(self, sid, folder):
        self.sid, self.folder = (sid, folder)
        self.name = 'pbe-behavioral-' + uuid.uuid4().hex[:12]
        self.events = queue.Queue()
        self.closed = False
        self.log = folder / ('engine-' + self.name + '.json')
        self.stderr = (folder / ('stderr-' + self.name + '.log')).open('wb')
        self.stdout = (folder / ('stdout-' + self.name + '.jsonl')).open('wb')
        self.requests = (folder / ('requests-' + self.name + '.jsonl')).open('wb')
        image = resolve_image(ROOT.parent.parent, load(ROOT / 'configuration.json')['images'][sid])
        self.command = ['docker', 'run', '--name', self.name, '--network', 'none', '--read-only', '--memory', '4g', '--memory-swap', '4g', '--cpus', '2', '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,exec,size=256m', '-e', 'PYTHONHASHSEED=0', '-e', 'PYTHONDONTWRITEBYTECODE=1', '--mount', f"type=bind,source={ROOT / 'code'},target=/evaluation,readonly", '--mount', f"type=bind,source={PREP / 'adapters'},target=/adapter,readonly", '-i']
        if sid in ['S01', 'S02', 'S06']:
            entry = 'python' if sid == 'S06' else 'python3'
            self.command += ['--entrypoint', entry, image, '-u', '/evaluation/execute_worker.py', sid]
        elif sid == 'S03':
            self.command += ['--mount', f'type=bind,source={RUNTIME},target=/prose,readonly', '--entrypoint', 'dotnet', image, '/prose/Qualification.dll']
        else:
            self.command += [image, 'execute-only']
        self.started = time.monotonic()
        self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)

        def reader():
            try:
                for line in self.process.stdout:
                    observed = time.monotonic()
                    self.stdout.write(line)
                    self.stdout.flush()
                    try:
                        result = json.loads(line)
                    except Exception as error:
                        result = {'invalid_json': repr(error), 'raw': line.decode('utf-8', errors='replace')}
                    self.events.put((observed, result))
            finally:
                self.events.put((time.monotonic(), None))
        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()
        try:
            self.ready = self.receive(self.started + 180)
            if self.ready.get('event', self.ready.get('event_type')) != 'ready':
                raise InfrastructureError('Missing ready event')
            if sid in ['S01', 'S02', 'S06', 'S08'] and self.ready.get('model_loaded') is not False:
                raise InfrastructureError('Unexpected learned model load on replay')
        except Exception:
            self.close(kill=True)
            raise
        self.initialization_seconds = time.monotonic() - self.started

    def receive(self, deadline):
        try:
            observed, value = self.events.get(timeout=max(0, deadline - time.monotonic()))
        except queue.Empty:
            raise Deadline()
        if observed > deadline:
            raise Deadline()
        if value is None:
            raise ProcessEnded()
        if 'invalid_json' in value:
            raise InfrastructureError(str(value))
        return value

    def execute(self, request_id, program, text):
        if self.sid in ['S01', 'S02', 'S06']:
            request = {'task_id': request_id, 'program': program, 'input': text}
        elif self.sid == 'S03':
            request = {'task_id': request_id, 'operation': 'execute', 'program': program, 'inputs': [text]}
        else:
            request = {'task_id': request_id, 'ast': program['ast'], 'inputs': [text]}
        data = (json.dumps(request, ensure_ascii=True) + '\n').encode('ascii')
        assert json.loads(data) == request
        self.requests.write(data)
        self.requests.flush()
        started = time.monotonic()
        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
            reply = self.receive(started + 15)
        except Deadline:
            self.close(kill=True)
            return {'status': 'execution_timeout', 'actual': None, 'seconds': time.monotonic() - started, 'engine': self.name, 'limit_seconds': 15}
        except (ProcessEnded, BrokenPipeError):
            self.close(kill=True)
            return {'status': 'execution_process_error', 'actual': None, 'seconds': time.monotonic() - started, 'engine': self.name, 'container_state': self.state}
        if reply.get('task_id') != request_id:
            raise InfrastructureError('Response ID mismatch')
        status, actual = (reply.get('status'), None)
        if self.sid in ['S01', 'S02', 'S06']:
            if reply.get('input_echo') != text:
                raise InfrastructureError('Input transport changed')
            if status == 'integration_error':
                raise InfrastructureError(json.dumps(reply, ensure_ascii=True))
            if status == 'returned':
                actual = reply['output']
                status = 'returned' if isinstance(actual, str) else 'non_string_output'
            elif status != 'execution_error':
                raise InfrastructureError('Unknown native wrapper status')
        elif status == 'executed':
            if self.sid == 'S03' and reply.get('roundtrip_equal') is not True:
                raise InfrastructureError('PROSE AST changed')
            if self.sid == 'S08' and reply.get('ast') != program['ast']:
                raise InfrastructureError('BUSTLE AST changed')
            if len(reply.get('outputs', [])) != 1:
                raise InfrastructureError('Output cardinality mismatch')
            actual = reply['outputs'][0]
            status = 'returned' if isinstance(actual, str) else 'non_string_output'
        elif status == 'adapter_error':
            if self.sid == 'S08' and 'Native operation undefined for input' in reply.get('error', ''):
                status = 'execution_error'
            elif self.sid == 'S03' and 'AstCodec.Load' not in reply.get('stack', '') and ('Run(' in reply.get('stack', '')):
                status = 'execution_error'
            else:
                raise InfrastructureError(json.dumps(reply, ensure_ascii=True))
        else:
            raise InfrastructureError('Unknown adapter response ' + str(reply))
        return {'status': status, 'actual': actual, 'seconds': time.monotonic() - started, 'engine': self.name, 'response': reply}

    def close(self, kill=False):
        if self.closed:
            return
        self.closed = True
        if kill:
            subprocess.run(['docker', 'kill', self.name], capture_output=True, timeout=20)
        try:
            self.process.stdin.close()
            self.process.wait(timeout=5)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            subprocess.run(['docker', 'kill', self.name], capture_output=True, timeout=20)
            self.process.wait(timeout=20)
        self.thread.join(timeout=5)
        inspection = subprocess.run(['docker', 'inspect', self.name, '--format', '{{json .State}}'], capture_output=True, timeout=20)
        self.state = json.loads(inspection.stdout) if inspection.returncode == 0 else {'inspection_error': inspection.stderr.decode(errors='replace')}
        subprocess.run(['docker', 'rm', '-f', self.name], capture_output=True, timeout=20)
        self.stdout.close()
        self.stderr.close()
        self.requests.close()
        save(self.log, {'command': self.command, 'ready': getattr(self, 'ready', None), 'initialization_seconds': getattr(self, 'initialization_seconds', None), 'container_state': self.state, 'exit_code': self.process.returncode})

def get_program(path):
    return load(path) if path.suffix == '.json' else path.read_text(encoding='utf-8')
from pbe.io import repository
from pbe.runtime_images import resolve_image
ROOT = repository() / 'runtimes/classical'
PREP = ROOT
RUNTIME = ROOT.parent / 'prose'
