from pathlib import Path
import json
import shutil
from .io import read, write, new_run, tasks_for, task_path, cases, verified_program, sha
from .analysis import report
from .runtime import ensure, required
from .assessment import INFRASTRUCTURE
from . import checkpoint
from uuid import uuid4
from .paths import execution_record, index_record, program_path


CLASSIC = {"synthphonia": "S01", "merlin": "S02", "prose": "S03", "crossbeam": "S06", "bustle": "S08"}


def engine_for(root, record, folder, image=None):
    if record["system"] in CLASSIC:
        from .systems.classical import Engine
        return Engine(CLASSIC[record["system"]], folder)
    from .systems.llm import Engine
    if record['system'] in {'direct-dsl','hysynth-string'} and record['runtime'] == 'hysynth-string':
        return Engine(folder/'candidate', folder, runtime='hysynth-string', image=image)
    if record["system"] != "direct-python" or record["runtime"] != "direct-python":
        raise ValueError("Unsupported program runtime.")
    return Engine(folder / "candidate", folder)


def prepare_candidate(root, record, folder):
    if record["system"] in CLASSIC:
        return
    out = folder / "candidate"
    out.mkdir(exist_ok=True)
    if record['system'] in {'direct-dsl','hysynth-string'} and record['runtime'] == 'hysynth-string':
        from .systems.hysynth.common import task_parts
        from .systems.hysynth.smt_transport import render
        _, synth = task_parts((root/record['grammar']).read_text(encoding='utf-8'), native=True)
        grammar = '(set-logic SLIA)\n'+render(synth, True)+'\n(constraint (= (f "") ""))\n(check-synth)\n'
        (out/'grammar.sl').write_text(grammar,encoding='utf-8',newline='\n')
        shutil.copy2(root/record['path'],out/'program.expr')
        return
    if record["system"] != "direct-python" or record["runtime"] != "direct-python":
        raise ValueError("Unsupported program runtime.")
    shutil.copy2(root / record["path"], out / "program.py")


def execute(engine, record, program, rid, value):
    if record["system"] in CLASSIC:
        return engine.execute(rid, program, value)
    return engine.execute(rid, value)


def evaluate(root, cfg, output=None, program_index=None, resume=False):
    if cfg.get("kind") == "synthesis":
        raise ValueError("Use the main experiment to evaluate the common cohort. synthesis-280 reports coverage.")
    if program_index is None and not cfg.get('programs'):
        raise ValueError('This experiment has no frozen programs yet. Supply --programs from a synthesis run, or use llm-dsl-pilot.')
    supported = {"cpus": 2, "memory_gib": 4, "initialization_seconds": 180, "case_seconds": 15, "retries": 0, "normalization": "none"}
    if any(cfg["evaluation"].get(k) != v for k, v in supported.items()):
        raise ValueError("The pinned runtime adapters require the recorded execution limits.")
    index_path = Path(program_index) if program_index else root / cfg["programs"]
    index = read(index_path)
    tasks = tasks_for(root, cfg)
    outcomes_path = index_path.parent / 'outcomes.json'
    outcomes = read(outcomes_path) if program_index and outcomes_path.exists() else []
    outcome_index = {}
    for row in outcomes:
        key = row['system'] + '/' + row['task_id']
        if key in outcome_index:
            raise ValueError('Duplicate synthesis outcome: ' + key)
        outcome_index[key] = row
    selected, missing = [], []
    for system in cfg["systems"]:
        for tid in cfg["task_ids"]:
            record = index.get(system + "/" + tid)
            outcome = outcome_index.get(system + '/' + tid)
            if record is None:
                if not program_index or (outcome and outcome.get('frozen')):
                    raise ValueError(f"No frozen program for {system}/{tid} despite a frozen-program selection.")
                missing.append({'system': system, 'task_id': tid,
                                'status': 'unresolved' if outcome and outcome.get('status') in INFRASTRUCTURE | {'interrupted', 'request_error'} else 'no_program' if outcome else 'pending',
                                'synthesis_status': outcome.get('status') if outcome else None})
                continue
            if record['system'] != system or record['task_id'] != tid:
                raise ValueError('Program index identity mismatch.')
            if outcome and not outcome.get('frozen'):
                raise ValueError('Program conflicts with synthesis outcome.')
            if cfg.get('study_run') and record.get('study_run') != cfg['study_run']:
                raise ValueError('Program belongs to a different study condition or repetition.')
            verified_program(root, record, index_path)
            selected.append(record)
    active_systems = list(dict.fromkeys(r['system'] for r in selected))
    images = ensure(root, active_systems, overrides=cfg.get("runtime_images")) if active_systems else {}
    out = checkpoint.folder(root, 'evaluate', output, resume)
    with checkpoint.lock(out):
        checkpoint.retain(out / 'selection.json', cfg)
        checkpoint.retain(out / 'outcomes.json', outcomes)
        checkpoint.retain(out / 'missing_programs.json', missing)
        stored = {r['system'] + '/' + r['task_id']:
                  index_record(r, program_path(root, r, index_path), out / 'programs.json') for r in selected}
        saved_index = out / 'programs.json'
        if resume and saved_index.exists():
            saved = read(saved_index)
            canonical = lambda records, path: {k: execution_record(root, r, path) for k, r in records.items()}
            if canonical(saved, saved_index) != canonical(stored, saved_index):
                raise ValueError('Evaluation program index changed.')
        else:
            checkpoint.retain(saved_index, stored)
        checkpoint.retain(out / 'provenance.json', {
            'runtime_images': {'pinned': required(root, active_systems, overrides=cfg.get('runtime_images')) if active_systems else {},
                               'resolved': images, 'original_pins': required(root, active_systems) if active_systems else {}},
            'program_index_sha256': sha(index_path),
            'task_hashes': {tid: sha(task_path(root, cfg, tid)) for tid in tasks},
            'code_hashes': {p.relative_to(root).as_posix(): sha(p) for p in (root / 'src').rglob('*.py')},
            'expected_outputs_sent_to_runtime': False, 'synthesis_calls': 0,
            'study_run': cfg.get('study_run'), 'run_id': cfg.get('run_id')})
        resolved = [execution_record(root, r, index_path) for r in selected]
        return execute_evaluation(root, cfg, out, resolved, missing, tasks, images)


def execute_evaluation(root, cfg, out, selected, missing, tasks, images):
    from .assessment import identity, validate_observations
    saved_predictions = checkpoint.journal(out / 'predictions.jsonl')
    saved_bases = checkpoint.journal(out / 'bases.jsonl')
    selected_keys = {(r['system'], r['task_id']) for r in selected}
    for row in saved_predictions + saved_bases:
        if (row['system'], row['task_id']) not in selected_keys:
            raise ValueError('Observation belongs to an unselected program.')
        if any(row.get(k) != v for k, v in identity(cfg, row['system']).items()):
            raise ValueError('Observation belongs to a different run.')
        if row['status'] in INFRASTRUCTURE:
            raise ValueError('Preserved observation records an infrastructure failure. Inspect it before resuming.')
    _, observed, base_observed = validate_observations(tasks, cfg['systems'], saved_predictions, saved_bases)
    complete = 0
    with (out / 'predictions.jsonl').open('a', encoding='utf-8', newline='\n') as predictions, (out / 'bases.jsonl').open('a', encoding='utf-8', newline='\n') as bases:
        for record in selected:
            system, tid = record['system'], record['task_id']
            task = tasks[tid]
            base_cases = task['behavioral'].get('bases', []) or [
                {'base_id': tid + '-B' + str(i+1), 'input': e['input'], 'expected_output': e['output']}
                for i, e in enumerate(task['split']['training'])]
            expected_cases = cases(task)
            engine = None
            receipt = out / 'completed' / system / (tid + '.json')
            try:
                for base in base_cases:
                    old = base_observed.get((system, tid, base['base_id']))
                    if old and (old['status'] != 'returned' or old['actual'] != base['expected_output']):
                        raise RuntimeError('Preserved base replay failed. Do not replace it by rerunning.')
                done = all((system, tid, b['base_id']) in base_observed for b in base_cases)
                done = done and all((system, tid, suite, cid) in observed for suite, cid in expected_cases)
                if receipt.exists():
                    checkpoint.retain(receipt, {'program_sha256': record['sha256']})
                if not done or not receipt.exists():
                    folder = out / 'execution' / system / tid / ('attempt-' + uuid4().hex)
                    folder.mkdir(parents=True)
                    prepare_candidate(root, record, folder)
                    program = verified_program(root, record)
                    engine = engine_for(root, record, folder, image=images.get(system))
                    for base in base_cases:
                        key = system, tid, base['base_id']
                        if key in base_observed:
                            continue
                        result = execute_checked(engine, record, program, base['base_id'], base['input'])
                        if result['status'] in INFRASTRUCTURE:
                            write(folder / 'infrastructure.json', {'case_id': base['base_id'], **result})
                            raise RuntimeError('Container infrastructure failed before a valid observation.')
                        row = {**identity(cfg, system), 'task_id': tid, 'base_id': base['base_id'],
                               'input': base['input'], 'expected': base['expected_output'], **result}
                        checkpoint.append(bases, row)
                        base_observed[key] = row
                        if result['status'] != 'returned' or result['actual'] != base['expected_output']:
                            raise RuntimeError('Frozen program no longer reproduces its synthesis examples: ' + system + '/' + tid)
                    for (suite, cid), case in expected_cases.items():
                        key = system, tid, suite, cid
                        if key in observed:
                            continue
                        if engine.closed:
                            engine = engine_for(root, record, folder, image=images.get(system))
                        result = execute_checked(engine, record, program, cid, case['input'])
                        if result['status'] in INFRASTRUCTURE:
                            write(folder / 'infrastructure.json', {'case_id': cid, **result})
                            raise RuntimeError('Container infrastructure failed before a valid observation.')
                        passed = result['status'] == 'returned' and isinstance(result['actual'], str) and result['actual'] == case['expected']
                        row = {**identity(cfg, system), 'task_id': tid, 'suite': suite, 'case_id': cid, **case, **result, 'passed': passed}
                        checkpoint.append(predictions, row)
                        observed[key] = row
                    engine.close()
                    if engine.state.get('inspection_error') or engine.process.returncode == 125:
                        raise RuntimeError('Container infrastructure failed.')
                checkpoint.retain(receipt, {'program_sha256': record['sha256']})
                complete += 1
                write(out / 'status.json', {'status': 'running', 'completed': complete, 'total': len(selected),
                    'selected_tasks': len(tasks), 'missing_programs': len(missing)})
                print(f'[{complete}/{len(selected)}] {system}/{tid}', flush=True)
            except BaseException as error:
                write(out / 'status.json', {'status': 'interrupted', 'completed': complete,
                    'system': system, 'task_id': tid, 'error': str(error)})
                raise
            finally:
                if engine:
                    engine.close()
    # A report interrupted during writing is kept separately before rebuilding it.
    if (out / 'report').exists():
        (out / 'report').rename(out / ('report-previous-' + uuid4().hex))
    report(root, cfg, source=out, output=out / 'report')
    write(out / 'status.json', {'status': 'completed', 'completed': complete, 'total': len(selected),
        'selected_tasks': len(tasks), 'missing_programs': len(missing)})
    return out


def execute_checked(engine, record, program, rid, value):
    result = execute(engine, record, program, rid, value)
    if engine.closed and (engine.state.get('inspection_error') or engine.process.returncode == 125):
        raise RuntimeError('Container infrastructure failed before an observation could be committed.')
    return result
