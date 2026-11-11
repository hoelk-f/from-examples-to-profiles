"""Pinned offline native runtime. No model or evaluation-set access."""
from pathlib import Path
import json
import subprocess
import time
import uuid
from .common import ROOT, AdapterError, read, save
from pbe.runtime_images import resolve_image


def search_resource_failure(action, record, stderr):
    if action != 'search' or record['returncode'] == 125 or record['container_state'].get('inspection_error'):
        return None
    if record['container_state'].get('OOMKilled') or (record['returncode'] != 0 and 'java.lang.OutOfMemoryError' in stderr):
        return 'out_of_memory'
    return None


def _call(case, logs, action, seconds=90, images=None):
    case, logs = Path(case).resolve(), Path(logs)
    logs.mkdir(parents=True, exist_ok=False)
    cfg = read(ROOT/'runtime.json')
    name = 'pbe-hysynth-v2-'+uuid.uuid4().hex[:12]
    command = ['docker', 'run', '--name', name, '--network', 'none', '--read-only',
        '--memory', '4g', '--memory-swap', '4g', '--cpus', '2', '--pids-limit', '256',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--workdir', '/tmp',
        '--mount', f'type=bind,source={case},target=/case,readonly']
    if action == 'inspect':
        command += ['--entrypoint', 'sh', resolve_image(ROOT.parent.parent, (images or {}).get('hysynth-inspection', cfg['inspection_image'])), '-c',
            'exec java -XX:ActiveProcessorCount=2 -cp "$(cat /opt/probe/runtime-classpath.txt)" sygus.PoolInspectMain']
    elif action == 'search':
        command += ['-e', 'PBE_COMPLETIONS=/case/completions.json', resolve_image(ROOT.parent.parent, (images or {}).get('hysynth-search', cfg['search_image'])),
                    'synthesize', '/case/task.sl', str(cfg['search_seconds'])]
    else:
        raise AdapterError('Unknown runtime action')
    started = time.monotonic()
    timeout = False
    with (logs/'stdout.txt').open('wb') as out, (logs/'stderr.txt').open('wb') as err:
        p = subprocess.Popen(command, stdout=out, stderr=err)
        try:
            p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timeout = True
            subprocess.run(['docker', 'kill', name], capture_output=True, timeout=20)
            p.wait(timeout=20)
        except BaseException:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
            p.wait(timeout=20)
            raise
    inspected = subprocess.run(['docker', 'inspect', name, '--format', '{{json .State}}'], capture_output=True, timeout=20)
    state = json.loads(inspected.stdout) if inspected.returncode == 0 else {'inspection_error': True}
    subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
    record = {'command': command, 'seconds': time.monotonic()-started, 'timeout': timeout,
              'returncode': p.returncode, 'container_state': state}
    record['resource_failure'] = search_resource_failure(action, record, (logs/'stderr.txt').read_text(errors='replace'))
    save(logs/'runtime.json', record)
    if p.returncode == 125 or state.get('inspection_error') or (state.get('OOMKilled') and not record['resource_failure']):
        raise AdapterError('Runtime infrastructure failure, see '+str(logs))
    if record['resource_failure']:
        return record, None
    events = []
    for line in (logs/'stdout.txt').read_text(encoding='utf-8').splitlines():
        if line.startswith('{'):
            events.append(json.loads(line))
    return record, events[-1] if events else None


def inspect_pool(case, logs, proposals, images=None, resume=False):
    job = {'mode': 'pool', 'proposals': proposals}
    save(Path(case)/'inspect.json', job)
    try:
        run, response = call(case, logs, 'inspect', images=images, resume=resume)
    finally:
        # Preserve each replay's input even when the working file is reused.
        save(Path(logs)/'inspection_request.json', job)
    if run['timeout'] or run['returncode'] != 0 or not response or response.get('status') != 'inspected':
        raise AdapterError('Native qualification failed, see '+str(logs))
    rows = response['proposals']
    if [r['sample_id'] for r in rows] != [p['sample_id'] for p in proposals]:
        raise AdapterError('Native qualification response identity mismatch')
    return rows


def search(case, logs, images=None, resume=False):
    run, response = call(case, logs, 'search', read(ROOT/'runtime.json')['search_wall_seconds'], images=images, resume=resume)
    if run.get('resource_failure') == 'out_of_memory':
        return {'status': 'out_of_memory', 'frozen': False}
    if run['timeout']:
        return {'status': 'search_timeout', 'frozen': False}
    if run['returncode'] != 0:
        raise AdapterError('Native search failed, see '+str(logs))
    if response and response.get('status') == 'no_program':
        return {'status': 'no_program_within_budget', 'frozen': False}
    if not response or response.get('status') != 'program' or not isinstance(response.get('expression'), str):
        raise AdapterError('Unexpected native search response')
    return response


def call(case, logs, action, seconds=90, images=None, resume=False):
    if not images and not resume:
        return _call(case, logs, action, seconds)
    from pbe.checkpoint import retain
    from pbe.io import sha
    case, logs = Path(case), Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    inputs = ['task.sl', 'inspect.json' if action == 'inspect' else 'completions.json']
    retain(logs / 'call.json', {'action': action, 'seconds': seconds, 'images': images,
        'inputs': {name: sha(case / name) for name in inputs}})
    if (logs / 'completed.json').exists():
        saved = read(logs / 'completed.json')
        if sha(logs / saved['stdout']) != saved['stdout_sha256']:
            raise AdapterError('Native stage checkpoint changed')
        if 'stderr' in saved and sha(logs / saved['stderr']) != saved['stderr_sha256']:
            raise AdapterError('Native stage checkpoint changed')
        return saved['runtime'], saved['response']
    attempt = logs / 'attempts' / f"{len(list((logs / 'attempts').glob('*'))):03}"
    run, response = _call(case, attempt, action, seconds, images)
    if not run['timeout'] and run['returncode'] != 0 and not run.get('resource_failure'):
        raise AdapterError('Native stage failed. Its attempt is preserved.')
    stdout = attempt / 'stdout.txt'
    stderr = attempt / 'stderr.txt'
    save(logs / 'completed.json', {'runtime': run, 'response': response,
        'stdout': stdout.relative_to(logs).as_posix(), 'stdout_sha256': sha(stdout),
        'stderr': stderr.relative_to(logs).as_posix(), 'stderr_sha256': sha(stderr)})
    return run, response
