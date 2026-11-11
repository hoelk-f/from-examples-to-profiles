"""Versioned evaluation-only plans for additional behavioral tests."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from .checkpoint import lock, retain
from .comparison import CLASSICAL
from .extension_cases import generate_task
from .io import digest, new_run, read, records, selection, sha, tasks_for, verified_program, write
from .paths import index_record, program_path
from .study import load as load_study


def reference(root, path):
    path = Path(path).resolve()
    return path.relative_to(root.resolve()).as_posix() if path.is_relative_to(root.resolve()) else str(path)


def code_hashes(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / 'src').rglob('*.py'))}


def plan(root, cfg, source, output=None):
    if cfg.get('kind') != 'behavioral_extension' or not cfg.get('evaluation_only'):
        raise ValueError('Choose a versioned evaluation-only extension experiment.')
    study, original = load_study(root, source, execution=False)
    classical = selection(root, cfg['classical_experiment'], ','.join(CLASSICAL))
    if original['experiment'] != cfg['source_study_experiment']:
        raise ValueError('The extension requires its configured original study version.')
    for key in ['task_ids', 'evaluation', 'examples_per_task']:
        if cfg[key] != original['config'][key] or cfg[key] != classical[key]:
            raise ValueError('Original and extension settings differ: ' + key)
    sources = {}

    def remember(path):
        sources[reference(root, path)] = sha(path)

    remember(study / 'study.json')
    remember(root / 'experiments' / (original['experiment'] + '.json'))
    remember(root / 'experiments' / (classical['id'] + '.json'))
    original_tasks = tasks_for(root, classical)
    for tid in cfg['task_ids']:
        remember(root / 'data/tasks' / (tid + '.json'))
    generated = {tid: generate_task(task, cfg['design']) for tid, task in original_tasks.items()}
    if not any(task['behavioral']['cases'] for task in generated.values()):
        raise ValueError('The extension generated no test cases.')
    out = new_run(root, 'extension', output)
    data = root / 'data' / cfg['id']
    for tid, task in generated.items():
        retain(data / 'tasks' / (tid + '.json'), task)
    task_set = {'directory': reference(root, data / 'tasks'),
                'hashes': {tid: sha(data / 'tasks' / (tid + '.json')) for tid in generated}}
    generation = {'experiment': cfg['id'], 'version': cfg['version'], 'design': cfg['design'],
        'source_task_hashes': original['task_hashes'], 'task_set': task_set,
        'case_count': sum(len(t['behavioral']['cases']) for t in generated.values()),
        'heldout_controls': sum(len(t['split']['heldout']) for t in generated.values()),
        'operators': {}, 'new_model_requests': 0, 'program_executions': 0}
    for op in ['S02', 'V06', 'V07']:
        rows = [ob for t in generated.values() for ob in t['behavioral']['obligations'] if ob['operator_id'] == op]
        generation['operators'][op] = {'statuses': dict(Counter(r['status'] for r in rows)),
            'cases': len({r['case_id'] for r in rows if r['status'] == 'planned'}),
            'applicable_tasks': len({r['task_id'] for r in rows if r['status'] == 'planned'}),
            'reasons': dict(Counter(r['reason'] for r in rows if 'reason' in r))}
    retain(data / 'manifest.json', generation)
    bound = {**deepcopy(cfg), 'evaluation_task_set': task_set}
    extension_id = uuid.uuid4().hex
    jobs = []
    candidates = [{'condition': 'classical/' + system, 'system': system, 'repeat': 1,
        'family': 'symbolic DSL synthesis' if system in CLASSICAL[:3] else 'neural-guided search',
        'model_slot': None, 'model': None, 'classical': True} for system in CLASSICAL] + original['jobs']
    for job in candidates:
        system, condition, repeat = job['system'], job['condition'], job['repeat']
        if job.get('classical'):
            index_path = root / classical['programs']
            evidence = root / 'results/published' / classical['id']
            saved = {}
            outcomes = [{'system': system, 'task_id': tid, 'frozen': True, 'status': 'frozen'} for tid in cfg['task_ids']]
        else:
            evidence = study / job['directory'] / 'evaluation'
            if read(evidence / 'status.json')['status'] != 'completed':
                raise ValueError('Original evaluation is incomplete: ' + condition)
            index_path = evidence / 'programs.json'
            saved = read(evidence / 'selection.json')
            if saved['study_run']['condition'] != condition or saved['study_run']['repeat'] != repeat:
                raise ValueError('Original condition identity mismatch.')
            outcomes = read(evidence / 'outcomes.json')
            for name in ['selection.json', 'outcomes.json', 'status.json']:
                remember(evidence / name)
        remember(index_path)
        observations = {}
        for name in ['predictions', 'bases']:
            path = next((evidence / (name + suffix) for suffix in ['.jsonl.gz', '.jsonl'] if (evidence / (name + suffix)).exists()), None)
            if path is None:
                raise ValueError('Missing original observations: ' + str(evidence))
            remember(path)
            observations[name] = reference(root, path)
        directory = 'jobs/' + condition + '/repeat-' + str(repeat)
        inputs = out / directory / 'inputs'
        job_cfg = {**deepcopy(bound), 'systems': [system], 'model': job['model'],
                   'extension_run': {'extension_id': extension_id, 'condition': condition, 'repeat': repeat}}
        for key in ['study_run', 'run_id', 'started_at']:
            if key in saved:
                job_cfg[key] = saved[key]
        index = {}
        for key, record in read(index_path).items():
            if record['system'] != system or record['task_id'] not in cfg['task_ids']:
                continue
            if saved and (record.get('study_run') != saved['study_run'] or record.get('run_id') != saved.get('run_id')):
                raise ValueError('Original program identity mismatch.')
            verified_program(root, record, index_path)
            program = program_path(root, record, index_path)
            remember(program)
            if record.get('grammar'):
                remember(root / record['grammar'])
            index[key] = index_record(record, program, inputs / 'programs.json')
        retain(inputs / 'selection.json', job_cfg)
        retain(inputs / 'programs.json', index)
        retain(inputs / 'outcomes.json', outcomes)
        jobs.append({**{k: job[k] for k in ['condition', 'system', 'family', 'model_slot', 'model', 'repeat']},
            'directory': directory, 'config': job_cfg, 'observations': observations,
            'input_hashes': {name: sha(inputs / name) for name in ['selection.json', 'programs.json', 'outcomes.json']},
            'programs': len(index)})
    manifest = {'schema_version': 1, 'extension_id': extension_id, 'experiment': cfg['id'], 'version': cfg['version'],
        'created_at': datetime.now(timezone.utc).isoformat(), 'config': bound, 'jobs': jobs,
        'experiment_sha256': sha(root / 'experiments' / (cfg['id'] + '.json')),
        'source_study_id': original['study_id'], 'source_plan_digest': original['plan_digest'],
        'source_files': sources, 'generation_manifest_sha256': sha(data / 'manifest.json'),
        'code_hashes': code_hashes(root), 'new_model_requests': 0, 'synthesis_calls': 0}
    manifest['plan_digest'] = digest(manifest)
    write(out / 'extension.json', manifest)
    write(out / 'generation.json', generation)
    load(root, out)
    print(f"Prepared {len(jobs)} frozen-program jobs and {generation['case_count']} additional inputs. No model requests. {out}")
    return out


def load(root, source, execution=True):
    path = Path(source)
    path = path / 'extension.json' if path.is_dir() else path
    manifest = read(path)
    if manifest['plan_digest'] != digest({k: v for k, v in manifest.items() if k != 'plan_digest'}):
        raise ValueError('Extension plan changed. Create a new version.')
    cfg = manifest['config']
    if not cfg.get('evaluation_only') or cfg['kind'] != 'behavioral_extension':
        raise ValueError('Not an evaluation-only extension plan.')
    if sha(root / 'experiments' / (cfg['id'] + '.json')) != manifest['experiment_sha256']:
        raise ValueError('Extension experiment changed.')
    for name, expected in manifest['source_files'].items():
        if sha(root / name) != expected:
            raise ValueError('Frozen source changed: ' + name)
    tasks_for(root, cfg)
    if sha(root / 'data' / cfg['id'] / 'manifest.json') != manifest['generation_manifest_sha256']:
        raise ValueError('Extension generation manifest changed.')
    for job in manifest['jobs']:
        inputs = path.parent / job['directory'] / 'inputs'
        for name, expected in job['input_hashes'].items():
            if sha(inputs / name) != expected:
                raise ValueError('Extension job input changed: ' + str(inputs / name))
    if execution and code_hashes(root) != manifest['code_hashes']:
        raise ValueError('Extension execution code changed. Use its pinned version.')
    return path.parent, manifest


def verify_replay(root, folder, job):
    from .assessment import identity, validate_observations, INFRASTRUCTURE
    from .paths import execution_record
    target = folder / job['directory'] / 'evaluation'
    if read(target / 'selection.json') != job['config'] or read(target / 'status.json')['status'] != 'completed':
        raise ValueError('Extension evaluation is incomplete or belongs to another job.')
    programs = read(target / 'programs.json')
    inputs = folder / job['directory'] / 'inputs/programs.json'
    original_programs = read(inputs)
    normalized = lambda entries, index: {key: execution_record(root, value, index) for key, value in entries.items()}
    if normalized(programs, target / 'programs.json') != normalized(original_programs, inputs):
        raise ValueError('Extension output program index differs from its pinned inputs.')
    for record in programs.values():
        verified_program(root, record, target / 'programs.json')
    present = {r['task_id'] for r in programs.values()}
    totals = {}
    observations = {}
    for kind in ['predictions', 'bases']:
        old = {}
        for row in records(root / job['observations'][kind]):
            if row['system'] != job['system'] or row['task_id'] not in present or (kind == 'predictions' and row['suite'] != 'heldout'):
                continue
            key = row['task_id'], row['case_id' if kind == 'predictions' else 'base_id']
            if key in old:
                raise ValueError('Duplicate original replay control.')
            old[key] = row
        observed = {}
        observations[kind] = list(records(target / (kind + '.jsonl')))
        for row in observations[kind]:
            if kind == 'predictions' and row['suite'] != 'heldout':
                continue
            key = row['task_id'], row['case_id' if kind == 'predictions' else 'base_id']
            if key in observed:
                raise ValueError('Duplicate extension replay control.')
            observed[key] = row
        if set(old) != set(observed):
            raise ValueError('Replay control coverage differs from the original.')
        for key, row in old.items():
            if any(row.get(k) != observed[key].get(k) for k in ['input', 'expected', 'status', 'actual']):
                raise ValueError('Frozen control output changed: ' + str((job['condition'], job['repeat'], key)))
        totals[kind] = len(old)
    cfg = job['config']
    tasks = tasks_for(root, cfg)
    expected, predictions, bases = validate_observations(tasks, cfg['systems'], observations['predictions'], observations['bases'])
    required = {(job['system'], tid, suite, cid) for tid in present for suite, cid in expected[tid]}
    required_bases = {(job['system'], tid, b['base_id']) for tid in present for b in tasks[tid]['behavioral']['bases']}
    if set(predictions) != required or set(bases) != required_bases:
        raise ValueError('Extension observation coverage is incomplete.')
    wanted = identity(cfg, job['system'])
    for row in observations['predictions'] + observations['bases']:
        if row['status'] in INFRASTRUCTURE or any(row.get(k) != v for k, v in wanted.items()):
            raise ValueError('Extension observation identity or infrastructure status is invalid.')
    result = {'condition': job['condition'], 'repeat': job['repeat'], 'programs': len(present),
        'heldout_outputs_identical': totals['predictions'], 'base_outputs_identical': totals['bases'],
        'new_model_requests': 0, 'synthesis_calls': 0,
        'evidence_hashes': {name: sha(target / name) for name in ['predictions.jsonl', 'bases.jsonl', 'programs.json', 'status.json']}}
    retain(target / 'replay-verification.json', result)
    return result


def run(root, source, resume=False, workers=1, condition=None, repeat=None):
    if workers < 1 or workers > 4:
        raise ValueError('Use one to four concurrent evaluation jobs.')
    folder, manifest = load(root, source)
    jobs = [j for j in manifest['jobs'] if (condition is None or j['condition'] == condition) and (repeat is None or j['repeat'] == repeat)]
    if not jobs:
        raise ValueError('No matching extension jobs.')
    for job in jobs:
        if (folder / job['directory'] / 'evaluation').exists() and not resume:
            raise ValueError('Evaluation output exists. Use --resume.')
    with lock(folder):
        finished, failed = [], []

        def execute(job):
            target = folder / job['directory'] / 'evaluation'
            if (target / 'status.json').exists() and read(target / 'status.json')['status'] == 'completed':
                return verify_replay(root, folder, job)
            command = [sys.executable, '-B', '-m', 'pbe', 'evaluate', '--programs',
                       str(folder / job['directory'] / 'inputs/programs.json'), '--output', str(target)]
            if target.exists():
                command.append('--resume')
            logs = folder / job['directory'] / 'logs'
            logs.mkdir(exist_ok=True)
            attempt = logs / (uuid.uuid4().hex + '.log')
            env = {**os.environ, 'PBE_ROOT': str(root), 'PYTHONPATH': str(root / 'src')}
            with attempt.open('w') as stream:
                result = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"Evaluation failed for {job['condition']} repeat {job['repeat']}. See {attempt}")
            return verify_replay(root, folder, job)

        write(folder / 'status.json', {'status': 'running', 'selected_jobs': len(jobs), 'completed_jobs': 0, 'workers': workers})
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(execute, job): job for job in jobs}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    finished.append(future.result())
                    print(f"[{len(finished)}/{len(jobs)}] {job['condition']} repeat {job['repeat']} completed and replay verified", flush=True)
                except Exception as error:
                    failed.append({'condition': job['condition'], 'repeat': job['repeat'], 'error': str(error)})
                    print(str(error), file=sys.stderr, flush=True)
                write(folder / 'status.json', {'status': 'running', 'selected_jobs': len(jobs),
                    'completed_jobs': len(finished), 'failed_jobs': failed, 'workers': workers, 'new_model_requests': 0})
        load(root, folder)
        complete_jobs = sum((folder / j['directory'] / 'evaluation/replay-verification.json').exists() for j in manifest['jobs'])
        write(folder / 'status.json', {'status': 'interrupted' if failed else 'completed' if complete_jobs == len(manifest['jobs']) else 'partial',
            'planned_jobs': len(manifest['jobs']), 'completed_jobs': complete_jobs, 'failed_jobs': failed,
            'new_model_requests': 0, 'synthesis_calls': 0})
        if failed:
            raise RuntimeError('Some extension evaluations need attention. Completed jobs are preserved for resume.')
    return folder


def report(root, source, output=None):
    from .extension_report import report_extension
    return report_extension(root, source, output)
