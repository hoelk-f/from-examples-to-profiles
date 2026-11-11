from datetime import datetime, timezone
import hashlib, json, queue, subprocess, threading, time, uuid
from pathlib import Path
from pbe.io import repository
from pbe.runtime_images import resolve_image
ROOT = repository() / 'runtimes/llm'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def lines(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_bytes((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    tmp.replace(path)

def now():
    return datetime.now(timezone.utc).isoformat()

class InfrastructureError(Exception):
    pass

class Engine:

    def __init__(self, candidate, logs, runtime='direct-python', image=None):
        if runtime not in {'direct-python','hysynth-string'}:
            raise ValueError('Unsupported LLM program runtime')
        self.closed = False
        self.name = 'pbe-sol-eval-' + uuid.uuid4().hex[:14]
        self.logs = logs
        self.events = queue.Queue()
        self.stderr = (logs / (self.name + '.stderr.txt')).open('wb')
        self.stdout = (logs / (self.name + '.stdout.jsonl')).open('wb')
        self.requests = (logs / (self.name + '.requests.jsonl')).open('wb')
        cfg = read(ROOT / 'configuration.json')
        cmd = ['docker', 'run', '--name', self.name, '--network', 'none', '--read-only', '--memory', '4g', '--memory-swap', '4g', '--cpus', '2', '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=256m', '--workdir', '/tmp', '-i', '--mount', f'type=bind,source={candidate},target=/candidate,readonly']
        if runtime == 'direct-python':
            cmd += ['--user', '65534:65534', '--mount', f"type=bind,source={ROOT / 'python_worker.py'},target=/worker.py,readonly", '--entrypoint', 'python', resolve_image(ROOT.parent.parent, cfg['images']['direct']), '-I', '-B', '-u', '/worker.py']
        else:
            image = resolve_image(ROOT.parent.parent, image or read(ROOT.parent/'hysynth/runtime.json')['evaluation_image'])
            cmd += ['--entrypoint','sh',image,'-c',
                    'exec java -XX:ActiveProcessorCount=2 -cp "$(cat /opt/probe/runtime-classpath.txt)" sygus.SolEvaluationWorker']
        self.cmd = cmd
        start = time.monotonic()
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)

        def reader():
            try:
                for line in self.process.stdout:
                    self.stdout.write(line)
                    self.stdout.flush()
                    try:
                        obj = json.loads(line)
                    except Exception:
                        obj = {'protocol_error': line.decode('utf-8', errors='replace')[:2000]}
                    self.events.put((time.monotonic(), obj))
            finally:
                self.events.put((time.monotonic(), None))
        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()
        try:
            ready = self.receive(start + cfg['initialization_timeout_seconds'])
            if ready != {'event': 'ready', 'model_loaded': False}:
                raise InfrastructureError('Unexpected initialization response ' + str(ready))
        except Exception:
            self.close(kill=True)
            raise
        self.initialization_seconds = time.monotonic() - start

    def receive(self, deadline):
        observed, obj = self.events.get(timeout=max(0, deadline - time.monotonic()))
        if observed > deadline:
            raise queue.Empty()
        if obj is None:
            raise EOFError('Worker ended')
        if 'protocol_error' in obj:
            raise InfrastructureError(str(obj))
        return obj

    def execute(self, rid, text):
        request = {'id': rid, 'input': text}
        data = (json.dumps(request, ensure_ascii=True) + '\n').encode('ascii')
        self.requests.write(data)
        self.requests.flush()
        start = time.monotonic()
        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
            response = self.receive(start + 15)
        except queue.Empty:
            self.close(kill=True)
            return {'status': 'execution_timeout', 'actual': None, 'seconds': time.monotonic() - start, 'engine': self.name}
        except (EOFError, BrokenPipeError):
            self.close(kill=True)
            return {'status': 'execution_process_error', 'actual': None, 'seconds': time.monotonic() - start, 'engine': self.name}
        if response.get('id') != rid or response.get('input_echo') != text:
            raise InfrastructureError('Input or request identity mismatch')
        status = response.get('status')
        if status not in ['returned', 'non_string_output', 'execution_error']:
            raise InfrastructureError('Unexpected worker status')
        actual = response.get('output') if status == 'returned' else None
        if status == 'returned' and (not isinstance(actual, str)):
            raise InfrastructureError('Invalid returned-output type')
        return {'status': status, 'actual': actual, 'seconds': time.monotonic() - start, 'engine': self.name, 'response': response}

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
        inspected = subprocess.run(['docker', 'inspect', self.name, '--format', '{{json .State}}'], capture_output=True, timeout=20)
        self.state = json.loads(inspected.stdout) if inspected.returncode == 0 else {'inspection_error': True}
        subprocess.run(['docker', 'rm', '-f', self.name], capture_output=True, timeout=20)
        self.stdout.close()
        self.stderr.close()
        self.requests.close()
        save(self.logs / (self.name + '.engine.json'), {'command': self.cmd, 'exit_code': self.process.returncode, 'initialization_seconds': getattr(self, 'initialization_seconds', None), 'container_state': self.state})
