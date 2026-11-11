"""Resume a fixed synthesis job without replacing completed model requests."""
from collections import Counter
from pathlib import Path
from uuid import uuid4
from . import checkpoint
from .io import read, write, sha, tasks_for, task_path, digest, verified_program
from .provider import Provider
from .runtime import ensure, CLASSIC
from .study import timestamp, validate_identity
from .synthesis import messages, path_ref
from .systems import dsl
from .paths import index_record, qualification_folder


def input_hashes(root, cfg):
    paths = set((root / 'src').rglob('*.py'))
    paths.update((root / 'runtimes').glob('*/configuration.json'))
    paths.update((root / 'runtimes').glob('*/runtime.json'))
    for tid in cfg['task_ids']:
        paths.add(task_path(root, cfg, tid))
        if 'direct-python' in cfg['systems']:
            paths.add(root / 'artifacts/llm/legacy/direct' / tid / 'request.json')
        if set(cfg['systems']) & dsl.SYSTEMS:
            paths.update((root / cfg['dsl']['tasks'] / tid).glob('*'))
    if set(cfg['systems']) & dsl.SYSTEMS:
        for key in ['plan', 'live_plan']:
            if key in cfg['dsl']:
                paths.add(root / cfg['dsl'][key])
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths) if p.is_file()}


def synthesize(root, cfg, output, live, provider_file, pool_dir, resume, retry_uncertain):
    if retry_uncertain and not (resume and live):
        raise ValueError('--retry-uncertain requires --resume and --live.')
    if live != bool(provider_file):
        raise ValueError('Use --live and --provider together.')
    systems = cfg['systems']
    if set(systems) - (set(CLASSIC) | {'direct-python'} | dsl.SYSTEMS):
        raise ValueError('Unsupported synthesis method.')
    if live and not set(systems) & ({'direct-python'} | dsl.SYSTEMS):
        raise ValueError('Selected systems do not use a model provider.')
    if pool_dir and (live or not set(systems) & dsl.SYSTEMS):
        raise ValueError('--pool-dir is only for recorded DSL synthesis.')
    config = read(provider_file) if provider_file else None
    validate_identity(cfg, config, live)
    tasks = tasks_for(root, cfg)
    preparations = {}
    dsl_systems = [s for s in systems if s in dsl.SYSTEMS]
    for tid, task in tasks.items():
        if dsl_systems:
            examples = [{'input': e['input'], 'output': e['output']} for e in task['split']['training']]
            preparations[tid] = dsl.prepared(root, cfg, tid, examples, pool_dir, live)
    count = len(tasks) if 'direct-python' in systems else 0
    count += sum(p['plan']['attempts_per_task'] for p in preparations.values())
    # Fail before creating the run when credentials, limits or runtimes are missing.
    if live:
        Provider(config, count)
    images = ensure(root, systems, synthesis=True, overrides=cfg.get('runtime_images'))
    out = checkpoint.folder(root, 'synthesize', output, resume)
    with checkpoint.lock(out):
        checkpoint.retain(out / 'checkpoint.json', {'config': cfg, 'provider': config, 'live': live,
            'input_hashes': input_hashes(root, cfg), 'resolved_images': images,
            'pool_hashes': {tid: sha(p['pool']) for tid, p in preparations.items()} if not live else {}})
        if (out / 'selection.json').exists():
            saved = read(out / 'selection.json')
            if saved.get('study_run') != cfg.get('study_run'):
                raise ValueError('Synthesis belongs to another study job.')
            cfg = saved
        else:
            cfg = {**cfg, 'run_id': uuid4().hex, 'started_at': timestamp()}
            if config:
                cfg['model'] = config['model']
            write(out / 'selection.json', cfg)
        if config:
            checkpoint.retain(out / 'provider.json', config)
        provider = Provider(config, count, out / 'request-ledger.json', retry_uncertain) if live else None
        index = read(out / 'programs.json') if (out / 'programs.json').exists() else {}
        outcomes = []
        if (out / 'programs.json').exists():
            for record in read(out / 'programs.json').values():
                verified_program(root, record, out / 'programs.json')
        active, tid = [], None
        try:
            for tid, task in tasks.items():
                examples = [{'input': e['input'], 'output': e['output']} for e in task['split']['training']]
                for system in systems:
                    active = [system]
                    done = out / 'completed' / system / (tid + '.json')
                    if done.exists():
                        saved = read(done)
                        if saved['digest'] != digest(saved['value']):
                            raise ValueError('Completed synthesis checkpoint changed.')
                        result = saved['value']['result']
                        folder = qualification_folder(out, saved['value']['folder'], system, tid)
                    else:
                        if system in CLASSIC:
                            from .systems.synthesis import run_one
                            folder = out / 'programs' / system / tid / ('attempt-' + uuid4().hex)
                            result = run_one(CLASSIC[system], {'task_id': tid, 'examples': examples}, folder)
                            if result['status'] in {'initialization_error', 'initialization_timeout', 'protocol_error', 'adapter_error'}:
                                raise RuntimeError('Synthesis stopped on an infrastructure failure.')
                        elif system in dsl.SYSTEMS:
                            results = dsl.run(preparations[tid], dsl_systems, out / 'dsl' / tid,
                                out / 'pools' / (tid + '.json'), provider, images=images,
                                resume=(out / 'dsl' / tid / 'processed').exists())
                            result, folder = results[system]
                        else:
                            from .systems.direct import direct
                            original = root / 'artifacts/llm/legacy/direct' / tid
                            answer = provider.complete(messages(read(original / 'request.json')),
                                out / 'requests' / system / tid)['text'] if live else (original / 'response.txt').read_text(encoding='utf-8')
                            base = out / 'programs' / system / tid
                            folder = base / ('attempt-' + uuid4().hex)
                            folder.mkdir(parents=True)
                            (folder / 'response.txt').write_text(answer, encoding='utf-8')
                            result = direct(read(root / 'runtimes/legacy/configuration.json'), folder, answer, examples)
                            write(folder / 'result.json', result)
                        value = {'result': result, 'folder': folder.relative_to(out).as_posix()}
                        write(done, {'value': value, 'digest': digest(value)})
                    key = system + '/' + tid
                    if result.get('frozen'):
                        path = folder / result['program_file']
                        if sha(path) != result['program_sha256']:
                            raise ValueError('Frozen synthesis checkpoint changed: ' + key)
                        index[key] = index_record({'system': system, 'task_id': tid,
                            'sha256': sha(path), 'runtime': system, 'run_id': cfg['run_id'], 'study_run': cfg.get('study_run')},
                            path, out / 'programs.json')
                        if system in dsl.SYSTEMS:
                            grammar = preparations[tid]['taskdir'] / 'task.native.sl'
                            index[key].update(runtime='hysynth-string', grammar=path_ref(root, grammar),
                                grammar_sha256=sha(grammar), pool_sha256=result['pool_sha256'])
                    outcomes.append({'system': system, 'task_id': tid, 'status': result['status'],
                        'frozen': result.get('frozen', False), 'run_id': cfg['run_id'], 'study_run': cfg.get('study_run')})
                    write(out / 'programs.json', index)
                    write(out / 'outcomes.json', outcomes)
                    print(system, tid, result['status'], flush=True)
            write(out / 'programs.json', index)
            write(out / 'outcomes.json', outcomes)
            write(out / 'status.json', {'status': 'completed', 'jobs': len(outcomes), 'frozen': len(index),
                'counts': dict(Counter(x['system'] + ':' + x['status'] for x in outcomes)),
                'new_model_requests': provider.completed if provider else 0, 'planned_requests': count if live else 0,
                'llm_source': 'live' if live else 'recorded', 'heldout_or_behavioral_answers_used': False,
                'finished_at': timestamp()})
        except BaseException as error:
            for system in active:
                if not any(r['system'] == system and r['task_id'] == tid for r in outcomes):
                    outcomes.append({'system': system, 'task_id': tid, 'status': 'interrupted', 'frozen': False,
                        'error_type': type(error).__name__, 'run_id': cfg['run_id'], 'study_run': cfg.get('study_run')})
            # Preserve completed later tasks when verification interrupts a resumed traversal.
            if (out / 'outcomes.json').exists():
                keys = {(r['system'], r['task_id']) for r in outcomes}
                outcomes += [r for r in read(out / 'outcomes.json') if (r['system'], r['task_id']) not in keys]
            write(out / 'outcomes.json', outcomes)
            write(out / 'status.json', {'status': 'interrupted', 'error_type': type(error).__name__,
                'completed_jobs': sum(r['status'] != 'interrupted' for r in outcomes),
                'new_model_requests': provider.completed if provider else 0})
            raise
    print(out)
    return out
