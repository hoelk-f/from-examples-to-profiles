"""Join fixed obligations with observations, including unfinished evaluations."""
from collections import Counter, defaultdict
import json
from .io import cases, digest, tasks_for, write
from .scoring import assertion_key, cells, score


EXECUTED = {'returned', 'execution_error', 'non_string_output', 'execution_timeout', 'execution_process_error'}
INFRASTRUCTURE = {'integration_error', 'initialization_error', 'initialization_timeout', 'protocol_error', 'adapter_error', 'infrastructure_error'}
FINISHED = {'passed', 'failed'}


def identity(cfg, system):
    study = cfg.get('study_run', {})
    return {'experiment': cfg['id'], 'experiment_version': cfg.get('version'),
            'condition': study.get('condition', system), 'system': system,
            'family': study.get('family', system), 'model_slot': study.get('model_slot'),
            'model': study.get('model', cfg.get('model') if system in {'direct-python', 'direct-dsl', 'hysynth-string'} else None), 'repeat': study.get('repeat'),
            'study_id': study.get('study_id'), 'run_id': cfg.get('run_id')}


def validate_observations(tasks, systems, predictions, bases):
    expected = {tid: cases(task) for tid, task in tasks.items()}
    index, base_index = {}, {}
    for row in predictions:
        system, tid = row['system'], row['task_id']
        if system not in systems or tid not in tasks:
            continue
        key = system, tid, row['suite'], row['case_id']
        case = expected[tid].get((row['suite'], row['case_id']))
        if key in index:
            raise ValueError('Duplicate prediction: ' + str(key))
        if case is None or row['input'] != case['input'] or row['expected'] != case['expected']:
            raise ValueError('Prediction does not match the fixed case: ' + str(key))
        validate_status(row)
        passed = row['status'] == 'returned' and isinstance(row.get('actual'), str) and row['actual'] == case['expected']
        if row['status'] in EXECUTED and 'passed' in row and row['passed'] != passed:
            raise ValueError('Stored verdict differs from recomputed exact match: ' + str(key))
        index[key] = row
    for row in bases:
        if row['system'] not in systems or row['task_id'] not in tasks:
            continue
        key = row['system'], row['task_id'], row['base_id']
        task = tasks[row['task_id']]
        targets = task['behavioral'].get('bases', []) or [
            {'base_id': task['task_id'] + '-B' + str(i + 1), 'input': e['input'], 'expected_output': e['output']}
            for i, e in enumerate(task['split']['training'])]
        target = next((b for b in targets if b['base_id'] == row['base_id']), None)
        if key in base_index or target is None or row['input'] != target['input'] or row['expected'] != target['expected_output']:
            raise ValueError('Invalid or duplicate base observation: ' + str(key))
        validate_status(row)
        base_index[key] = row
    return expected, index, base_index


def validate_status(row):
    if row['status'] not in EXECUTED | INFRASTRUCTURE:
        raise ValueError('Unknown observation status: ' + row['status'])


def verdict(assertion, variant, base, missing):
    if variant is None:
        return missing, None
    if variant['status'] in INFRASTRUCTURE:
        return 'unresolved', None
    if assertion['expectation'] != 'Exact Output':
        if base is None:
            return 'pending', None
        if base['status'] in INFRASTRUCTURE:
            return 'unresolved', None
    passed = score(assertion, variant, base)
    return ('passed' if passed else 'failed'), passed


def counts(states):
    counter = Counter(states)
    return {'planned': sum(counter.values()), 'executed': counter['passed'] + counter['failed'],
            **{name: counter[name] for name in ['passed', 'failed', 'pending', 'unresolved', 'no_program']}}


def task_metric(values):
    result = counts(values)
    complete = result['planned'] > 0 and result['executed'] == result['planned']
    return {**result, 'complete': complete,
            'accuracy': result['passed'] / result['planned'] if complete else None,
            'observed_accuracy': result['passed'] / result['executed'] if result['executed'] else None,
            'fully_passed': result['failed'] == 0 if complete else None}


def aggregate(bytask):
    rows = [task_metric(v.values()) for v in bytask.values() if v]
    total = {key: sum(r[key] for r in rows) for key in ['planned', 'executed', 'passed', 'failed', 'pending', 'unresolved', 'no_program']}
    complete = bool(rows) and all(r['complete'] for r in rows)
    completed = [r for r in rows if r['complete']]
    return {**total, 'tasks': len(rows), 'completed_tasks': len(completed), 'cases': total['planned'],
            'correct': total['passed'], 'complete': complete,
            'macro': sum(r['accuracy'] for r in rows) / len(rows) if complete else None,
            'micro': total['passed'] / total['planned'] if complete else None,
            'observed_micro': total['passed'] / total['executed'] if total['executed'] else None,
            'completed_task_macro': sum(r['accuracy'] for r in completed) / len(completed) if completed else None,
            'fully_passing_tasks': sum(r['fully_passed'] is True for r in rows)}


def assess(root, cfg, predictions, bases, programs=None, outcomes=None):
    tasks = tasks_for(root, cfg)
    if cfg.get('study_run'):
        predictions, bases = list(predictions), list(bases)
        for row in predictions + bases:
            if row['system'] in cfg['systems'] and row['task_id'] in tasks:
                meta = identity(cfg, row['system'])
                if any(row.get(k) != meta[k] for k in ['condition', 'model', 'repeat', 'study_id', 'run_id']):
                    raise ValueError('Observation belongs to another condition or repetition.')
        for record in (programs or {}).values():
            if record['system'] in cfg['systems'] and record['task_id'] in tasks:
                if record.get('study_run') != cfg['study_run'] or record.get('run_id') != cfg.get('run_id'):
                    raise ValueError('Program belongs to another condition or repetition.')
    expected, index, base_index = validate_observations(tasks, cfg['systems'], predictions, bases)
    programs = programs or {}
    outcome_index = {}
    observed_tasks = {key[:2] for key in index}
    for row in outcomes or []:
        key = row['system'], row['task_id']
        if key in outcome_index:
            raise ValueError('Duplicate synthesis outcome: ' + str(key))
        if key[0] in cfg['systems'] and key[1] in tasks:
            record = programs.get('/'.join(key))
            if record and not row.get('frozen'):
                raise ValueError('Program conflicts with synthesis outcome: ' + str(key))
            if row.get('frozen') and not record:
                raise ValueError('Frozen synthesis outcome has no program: ' + str(key))
            outcome_index[key] = row
    assertions, obligations, task_rows, profile_tasks, profiles, synthesis_rows = [], [], [], [], [], []
    suites = defaultdict(lambda: defaultdict(dict))
    buckets = defaultdict(lambda: defaultdict(dict))
    for system in cfg['systems']:
        meta = identity(cfg, system)
        for tid, task in tasks.items():
            program = programs.get(system + '/' + tid, {})
            if program and (program['system'] != system or program['task_id'] != tid):
                raise ValueError('Program index identity mismatch.')
            outcome = outcome_index.get((system, tid), {})
            known_absent = bool(outcome) and not outcome.get('frozen')
            if known_absent and (system, tid) in observed_tasks:
                raise ValueError('Observations exist for a task without a program: ' + tid)
            missing = 'unresolved' if known_absent and outcome.get('status') in INFRASTRUCTURE | {'interrupted', 'request_error'} else 'no_program' if known_absent else 'pending'
            synthesis_rows.append({**meta, 'task_id': tid, 'program_available': bool(program),
                'synthesis_status': outcome.get('status', 'frozen' if program else 'unknown'),
                'program_path': program.get('path'), 'program_sha256': program.get('sha256')})
            common = {**meta, 'task_id': tid, 'program_path': program.get('path'),
                      'program_sha256': program.get('sha256')}

            def joined(suite, cid, assertion, ob=None):
                variant = index.get((system, tid, suite, cid))
                base = base_index.get((system, tid, assertion.get('base_id')))
                state, passed = verdict(assertion, variant, base, missing)
                key = assertion_key(ob, assertion) if ob else ('exact', cid)
                wanted = assertion.get('expected_output')
                if assertion['expectation'] == 'Invariance' and base:
                    wanted = base.get('actual') if base['status'] == 'returned' else None
                elif assertion['expectation'] == 'Equivariance' and base:
                    value = base.get('actual')
                    start, end = assertion['start'], assertion['end']
                    if base['status'] == 'returned' and isinstance(value, str) and 0 <= start <= end <= len(value):
                        wanted = value[:start] + assertion['replacement'] + value[end:]
                return {**common, 'suite': suite, 'case_id': cid, 'check_id': digest(key),
                    'obligation_id': ob.get('obligation_id') if ob else None,
                    'assertion_id': assertion.get('assertion_id'), 'expectation': assertion['expectation'],
                    'operator': ob.get('operator_id') if ob else None, 'dimension': ob.get('dimension') if ob else None,
                    'profile_cells': cells(ob, assertion) if ob else [], 'regime': ob.get('regime') if ob else None,
                    'assertion': assertion, 'parameter': ob.get('parameter') if ob else None,
                    'requirement_scope': ob.get('requirement_scope') if ob else None,
                    'base_input': base.get('input') if base else None,
                    'input': expected[tid][suite, cid]['input'],
                    'expected_output': expected[tid][suite, cid]['expected'], 'expected_assertion_output': wanted,
                    'actual': variant.get('actual') if variant else None,
                    'observation_status': variant.get('status') if variant else None,
                    'base_id': assertion.get('base_id'), 'base_actual': base.get('actual') if base else None,
                    'base_expected': base.get('expected') if base else None,
                    'base_status': base.get('status') if base else None, 'status': state, 'passed': passed}

            for (suite, cid), case in expected[tid].items():
                row = joined(suite, cid, {'expectation': 'Exact Output', 'expected_output': case['expected']})
                suites[system, suite][tid][row['check_id']] = row['status']
                if suite == 'heldout':
                    assertions.append(row)
            for ob in task['behavioral'].get('obligations', []):
                state = ob.get('status', 'unresolved')
                if state == 'planned':
                    rows = [joined('behavioral', ob['case_id'], a, ob) for a in ob['assertions']]
                    assertions.extend(rows)
                    states = [r['status'] for r in rows]
                    execution = 'executed' if states and all(s in FINISHED for s in states) else next(
                        (s for s in ['unresolved', 'no_program', 'pending'] if s in states), 'unresolved')
                    for row in rows:
                        for cell in row['profile_cells']:
                            buckets[(system, *cell)][tid][row['check_id']] = row['status']
                else:
                    execution = 'unselected' if state == 'unselected' else 'inapplicable' if state in {'not_applicable_to_operator', 'inapplicable', 'not_applicable'} else 'unresolved'
                obligations.append({**common, 'obligation_id': ob['obligation_id'], 'operator': ob['operator_id'],
                    'dimension': ob['dimension'], 'planning_status': state, 'execution_status': execution,
                    'case_id': ob.get('case_id'), 'regime': ob.get('regime'),
                    'regime_statuses': {k: v.get('status', 'assigned' if 'value' in v else 'unclear') for k, v in ob.get('regime', {}).items()}})
            for suite in ['heldout', 'behavioral']:
                task_rows.append({**common, 'suite': suite, **task_metric(suites[system, suite][tid].values())})
    for (system, dimension, family, regime, expectation), bytask in sorted(buckets.items()):
        cell = {'dimension': dimension, 'regime_family': family, 'regime': regime, 'expectation': expectation}
        profiles.append({**identity(cfg, system), **cell, **aggregate(bytask)})
        for tid, values in bytask.items():
            profile_tasks.append({**identity(cfg, system), **cell, 'task_id': tid, **task_metric(values.values())})
    system_rows = []
    for system in cfg['systems']:
        obs = Counter(o['execution_status'] for o in obligations if o['system'] == system)
        status_counts = Counter(r['synthesis_status'] for r in synthesis_rows if r['system'] == system)
        check_states = {(r['task_id'], r['suite'], r['check_id']): r['status'] for r in assertions if r['system'] == system}
        regime_counts = Counter((k, v) for o in obligations if o['system'] == system for k, v in o['regime_statuses'].items())
        system_rows.append({**identity(cfg, system), 'task_count': len(tasks),
            'synthesis': {'tasks': len(tasks), 'programs': sum(r['program_available'] for r in synthesis_rows if r['system'] == system), 'statuses': dict(status_counts)},
            'obligations': {'total': sum(obs.values()), **{k: obs[k] for k in ['executed', 'pending', 'no_program', 'unresolved', 'unselected', 'inapplicable']}},
            'checks': counts(check_states.values()),
            'regime_annotations': [{'family': k, 'status': v, 'obligations': n} for (k, v), n in sorted(regime_counts.items())],
            **{suite: aggregate(suites[system, suite]) for suite in ['heldout', 'behavioral']}})
    return {'schema_version': 1, 'experiment': cfg['id'], 'task_count': len(tasks), 'systems': system_rows,
            'complete': all(r['checks']['executed'] == r['checks']['planned'] for r in system_rows),
            'assertions': assertions, 'obligation_rows': obligations, 'task_rows': task_rows,
            'profiles': profiles, 'profile_tasks': profile_tasks, 'synthesis_rows': synthesis_rows}


def jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')


def export(out, result):
    from .analysis import csv_write
    for name, key in [('assertions', 'assertions'), ('obligations', 'obligation_rows'), ('profile_tasks', 'profile_tasks')]:
        jsonl(out / (name + '.jsonl'), result[key])
    for name, key in [('task_metrics', 'task_rows'), ('coverage_profiles', 'profiles'), ('synthesis', 'synthesis_rows')]:
        csv_write(out / (name + '.csv'), result[key])
        write(out / (name + '.json'), result[key])
    csv_write(out / 'assertions.csv', [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                                       for k, v in row.items()} for row in result['assertions']])
    write(out / 'coverage.json', {k: result[k] for k in ['schema_version', 'experiment', 'task_count', 'complete', 'systems']})


def coverage_text(result):
    lines = ['Coverage of the fixed task cohort', 'Missing observations have no pass/fail verdict. Partial rates describe observed checks only.']
    for row in result['systems']:
        c, ob = row['checks'], row['obligations']
        lines.append(f"{row['system']}: {row['synthesis']['programs']}/{row['task_count']} programs, {c['executed']}/{c['planned']} checks executed, {c['pending']} pending, {c['no_program']} without a program, {c['unresolved']} unresolved.")
        lines.append(f"Obligations: {ob['executed']} executed, {ob['pending']} pending, {ob['no_program']} without a program, {ob['unresolved']} unresolved, {ob['unselected']} unselected, {ob['inapplicable']} inapplicable.")
    return '\n'.join(lines) + '\n'
