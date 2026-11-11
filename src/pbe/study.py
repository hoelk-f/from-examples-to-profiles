"""Prepare and run the repeated LLM study through explicit, bounded jobs."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import uuid
from .io import digest, new_run, read, selection, sha, write, task_path


from .provider import PARAMETERS
from .checkpoint import lock, retain


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def plan(root, cfg, output=None, bindings=None):
    design = cfg.get('study')
    if not design:
        raise ValueError('Choose a repeated-study experiment.')
    if bindings is None and cfg.get('provider_bindings'):
        bindings = root / cfg['provider_bindings']
    configs = read(bindings) if bindings else {}
    slots = design['model_slots']
    if configs and set(configs) != set(slots):
        raise ValueError('Bind exactly the configured model slots: ' + ', '.join(slots))
    for slot, config in configs.items():
        required = {'endpoint', 'model', 'api_key_env', 'max_requests', 'max_tokens'}
        if required - set(config) or not config['endpoint'].startswith('https://'):
            raise ValueError('Incomplete provider binding for ' + slot)
        if config['model'].startswith('SET_') or config.get('provider', {}).get('allow_fallbacks', False):
            raise ValueError('Choose an explicit model without provider fallback.')
        if config['max_tokens'] <= 0:
            raise ValueError('max_tokens must be positive.')
        if set(config) - {'name', 'endpoint', 'model', 'api_key_env', 'max_requests', *PARAMETERS}:
            raise ValueError('Unsupported provider keys. Store credentials only in the named environment variable.')
    if configs and len({c['model'] for c in configs.values()}) != len(slots):
        raise ValueError('Model slots must name distinct models.')
    jobs = []
    for method in design['methods']:
        requests = len(cfg['task_ids']) * method['requests_per_task']
        for slot in slots:
            config = configs.get(slot)
            if config and config['max_requests'] < requests:
                raise ValueError('Planned requests exceed the configured limit for ' + slot)
            for repeat in range(1, design['repetitions'] + 1):
                condition = method['system'] + '/' + slot
                jobs.append({'condition': condition, 'system': method['system'], 'family': method['family'],
                    'model_slot': slot, 'model': config['model'] if config else None, 'repeat': repeat,
                    'planned_requests': requests, 'directory': f"jobs/{method['system']}/{slot}/repeat-{repeat}"})
    out = new_run(root, 'study', output)
    manifest = {'schema_version': 1, 'study_id': uuid.uuid4().hex, 'created_at': timestamp(),
        'status': 'ready' if configs else 'awaiting_model_bindings', 'experiment': cfg['id'],
        'experiment_sha256': sha(root / 'experiments' / (cfg['id'] + '.json')),
        'config': cfg, 'providers': configs, 'jobs': jobs,
        'task_hashes': {tid: sha(task_path(root, cfg, tid)) for tid in cfg['task_ids']},
        'planned_requests': sum(j['planned_requests'] for j in jobs), 'new_model_requests': 0}
    if cfg.get('resume_protocol') == 1:
        from .resumable import input_hashes
        manifest['input_hashes'] = input_hashes(root, cfg)
        manifest['provider_compatibility'] = 'unverified_no_live_requests'
        manifest['maximum_http_submissions'] = manifest['planned_requests'] + sum(
            configs[j['model_slot']].get('max_extra_requests', 0) for j in jobs) if configs else None
    manifest['plan_digest'] = digest(manifest)
    if cfg.get('comparison_reference'):
        from .replacement import reference
        reference(root, manifest)
    write(out / 'study.json', manifest)
    print(f"Prepared {len(jobs)} jobs on {len(cfg['task_ids'])} tasks. No model requests made. {out}")
    return out


def load(root, source, *, execution=True):
    path = Path(source)
    path = path / 'study.json' if path.is_dir() else path
    manifest = read(path)
    if manifest.get('plan_digest') != digest({k: v for k, v in manifest.items() if k != 'plan_digest'}):
        raise ValueError('Study plan changed. Create a new plan instead.')
    cfg = manifest['config']
    selection(root, cfg['id'])
    if sha(root / 'experiments' / (cfg['id'] + '.json')) != manifest['experiment_sha256']:
        raise ValueError('Study experiment changed. Create a new version.')
    for tid, expected in manifest['task_hashes'].items():
        if sha(task_path(root, cfg, tid)) != expected:
            raise ValueError('Study task changed: ' + tid)
    if 'input_hashes' in manifest:
        from .resumable import input_hashes
        actual, expected = input_hashes(root, cfg), manifest['input_hashes']
        if not execution:
            actual = {k: v for k, v in actual.items() if not k.startswith('src/')}
            expected = {k: v for k, v in expected.items() if not k.startswith('src/')}
        if actual != expected:
            raise ValueError('Study code or synthesis inputs changed. Use the pinned execution version or create a new plan.')
    if execution and cfg.get('comparison_reference'):
        from .replacement import reference
        reference(root, manifest)
    return path.parent, manifest


def job_config(manifest, job):
    cfg = deepcopy(manifest['config'])
    provider = manifest['providers'].get(job['model_slot'])
    cfg['systems'] = [job['system']]
    cfg['model'] = job['model']
    cfg['study_run'] = {key: job[key] for key in ['condition', 'system', 'family', 'model_slot', 'model', 'repeat']}
    cfg['study_run'].update(study_id=manifest['study_id'], plan_digest=manifest['plan_digest'],
        provider_digest=digest(provider) if provider else None)
    return cfg


def validate_identity(cfg, provider=None, live=False):
    if not cfg.get('study'):
        return
    info = cfg.get('study_run')
    if not info or not info.get('model'):
        raise ValueError('Repeated synthesis requires a bound study job. Use study plan and study run.')
    if not live:
        raise ValueError('Recorded responses cannot be counted as independent study repetitions.')
    if digest(provider) != info['provider_digest'] or provider['model'] != info['model']:
        raise ValueError('Provider differs from the bound study condition.')


def run(root, source, live=False, condition=None, repeat=None, resume=False, retry_uncertain=False):
    folder, manifest = load(root, source)
    if retry_uncertain and not resume:
        raise ValueError('--retry-uncertain requires --resume.')
    with lock(folder):
        return run_jobs(root, folder, manifest, live, condition, repeat, resume, retry_uncertain)


def run_jobs(root, folder, manifest, live, condition, repeat, resume, retry_uncertain):
    if not live:
        raise ValueError('Study execution makes new model requests and requires explicit --live.')
    if manifest['status'] != 'ready':
        raise ValueError('Model slots are unbound. Create a new plan with --bindings.')
    jobs = [j for j in manifest['jobs'] if (condition is None or j['condition'] == condition)
            and (repeat is None or j['repeat'] == repeat)]
    if not jobs:
        raise ValueError('No matching study jobs.')
    from .synthesis import synthesize
    from .evaluation import evaluate
    for job in jobs:
        target = folder / job['directory']
        cfg = job_config(manifest, job)
        if (target / 'evaluation/status.json').exists() and read(target / 'evaluation/status.json')['status'] == 'completed':
            saved = read(target / 'evaluation/selection.json')
            if saved.get('study_run') != cfg['study_run'] or saved['task_ids'] != cfg['task_ids']:
                raise ValueError('Completed evaluation belongs to a different study job.')
            continue
        synthesis = target / 'synthesis'
        provider_path = target / 'provider.json'
        retain(provider_path, manifest['providers'][job['model_slot']])
        if synthesis.exists():
            if not (synthesis / 'status.json').exists() or read(synthesis / 'status.json')['status'] != 'completed':
                if not resume:
                    raise ValueError('An interrupted synthesis job exists. Use --resume for a resumable experiment: ' + str(synthesis))
                synthesize(root, cfg, synthesis, live=True, provider_file=provider_path,
                    resume=True, retry_uncertain=retry_uncertain)
            saved = read(synthesis / 'selection.json')
            if saved.get('study_run') != cfg['study_run']:
                raise ValueError('Saved synthesis belongs to a different study job.')
            cfg = saved
        else:
            synthesize(root, cfg, synthesis, live=True, provider_file=provider_path)
            cfg = read(synthesis / 'selection.json')
        if (target / 'evaluation').exists():
            if not resume:
                raise ValueError('Partial evaluation preserved. Use --resume: ' + str(target / 'evaluation'))
            evaluate(root, cfg, target / 'evaluation', synthesis / 'programs.json', resume=True)
        else:
            evaluate(root, cfg, target / 'evaluation', synthesis / 'programs.json')
    return folder
