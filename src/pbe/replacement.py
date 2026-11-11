"""Compare a new model study with unchanged historical model runs."""
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
from .assessment import INFRASTRUCTURE
from .io import new_run, read, selection, sha, verified_program, write
from .study import job_config, load


def reference(root, manifest):
    spec = manifest['config'].get('comparison_reference')
    if not spec:
        return None
    folder, baseline = load(root, root / spec['study'], execution=False)
    if sha(folder / 'study.json') != spec['study_sha256']:
        raise ValueError('Comparison reference study changed.')
    if spec.get('evidence_hashes'):
        from .comparison import evidence_hashes
        if evidence_hashes(root, folder, baseline) != spec['evidence_hashes']:
            raise ValueError('Pinned comparison reference evidence changed.')
    cfg, original = manifest['config'], baseline['config']
    for key in ['task_ids', 'examples_per_task', 'evaluation']:
        if cfg.get(key) != original.get(key):
            raise ValueError('Replacement and reference study differ: ' + key)
    for key in ['repetitions', 'methods']:
        if cfg['study'][key] != original['study'][key]:
            raise ValueError('Replacement and reference design differ: ' + key)
    if manifest['task_hashes'] != baseline['task_hashes']:
        raise ValueError('Replacement and reference task hashes differ.')
    slots = spec['model_slots']
    if not slots or len(set(slots)) != len(slots) or not set(slots) <= set(original['study']['model_slots']):
        raise ValueError('Unknown or duplicate reference model slots.')
    if set(slots) & set(cfg['study']['model_slots']):
        raise ValueError('New and reused model slots must be distinct.')
    return folder, baseline, slots


def job_availability(root, folder, manifest, job):
    task_ids = set(manifest['config']['task_ids'])
    cfg = job_config(manifest, job)
    target = folder / job['directory']
    evidence = target / 'evaluation' if (target / 'evaluation/selection.json').is_file() else target / 'synthesis'
    if (evidence / 'selection.json').is_file():
        saved = read(evidence / 'selection.json')
        if saved.get('study_run') != cfg['study_run'] or saved['task_ids'] != cfg['task_ids']:
            raise ValueError('Cohort evidence belongs to a different study job.')
        cfg = saved
    programs = read(evidence / 'programs.json') if (evidence / 'programs.json').exists() else {}
    outcomes = read(evidence / 'outcomes.json') if (evidence / 'outcomes.json').exists() else []
    present, absent, observed = set(), set(), set()
    for record in programs.values():
        if record['system'] != job['system'] or record['task_id'] not in task_ids:
            raise ValueError('Cohort program belongs to another method or task.')
        if record.get('study_run') != cfg['study_run'] or record.get('run_id') != cfg.get('run_id'):
            raise ValueError('Cohort program belongs to another repetition.')
        verified_program(root, record, evidence / 'programs.json')
        present.add(record['task_id'])
    unresolved = INFRASTRUCTURE | {'pending', 'interrupted', 'request_error', 'unknown'}
    for row in outcomes:
        tid = row['task_id']
        if row['system'] != job['system'] or tid not in task_ids or tid in observed:
            raise ValueError('Invalid cohort synthesis outcome.')
        observed.add(tid)
        if row.get('frozen') and tid not in present:
            raise ValueError('Frozen cohort outcome has no program.')
        if not row.get('frozen') and row.get('status') not in unresolved:
            if tid in present:
                raise ValueError('Failed cohort qualification conflicts with a program.')
            absent.add(tid)
    pending = task_ids - present - absent
    return {'condition': job['condition'], 'repeat': job['repeat'], 'source_study_id': manifest['study_id'],
            'qualified': sorted(present), 'not_qualified': sorted(absent), 'pending': sorted(pending),
            'qualification_complete': not pending}


def intersection(rows, task_ids):
    confirmed, possible = set(task_ids), set(task_ids)
    for row in rows:
        confirmed &= set(row['qualified'])
        possible -= set(row['not_qualified'])
    return {'confirmed_count': len(confirmed), 'confirmed_task_ids': sorted(confirmed),
            'possible_count': len(possible), 'possible_task_ids': sorted(possible),
            'excluded_task_ids': sorted(set(task_ids) - possible),
            'final': all(row['qualification_complete'] for row in rows)}


def report_cohort(root, source, output=None):
    from .comparison import CLASSICAL
    folder, manifest = load(root, source, execution=False)
    ref = reference(root, manifest)
    if not ref:
        raise ValueError('Choose a study with a pinned comparison_reference.')
    old_folder, old, slots = ref
    task_ids = manifest['config']['task_ids']
    classical = selection(root, 'main', ','.join(CLASSICAL))
    for key in ['task_ids', 'examples_per_task', 'evaluation']:
        if classical.get(key) != manifest['config'].get(key):
            raise ValueError('Classical and replacement cohort settings differ: ' + key)
    index_path = root / classical['programs']
    index = read(index_path)
    rows = []
    for system in CLASSICAL:
        present = []
        for tid in task_ids:
            record = index.get(system + '/' + tid)
            if record is None:
                raise ValueError('Missing fixed classical program: ' + system + '/' + tid)
            verified_program(root, record, index_path)
            present.append(tid)
        rows.append({'condition': 'classical/' + system, 'repeat': 1, 'source_study_id': None,
                     'qualified': present, 'not_qualified': [], 'pending': [], 'qualification_complete': True})
    old_rows = [job_availability(root, old_folder, old, j) for j in old['jobs']]
    baseline_rows = rows + [r for r, j in zip(old_rows, old['jobs']) if j['model_slot'] in slots]
    if not all(r['qualification_complete'] for r in baseline_rows):
        raise ValueError('The reused baseline qualification is incomplete.')
    new_rows = [job_availability(root, folder, manifest, j) for j in manifest['jobs']]
    combined = baseline_rows + new_rows
    grouped = defaultdict(list)
    for row in combined:
        grouped[row['condition']].append(row)
    result = {'experiment': manifest['experiment'], 'study_id': manifest['study_id'],
        'observed_at': datetime.now(timezone.utc).isoformat(), 'tasks': len(task_ids),
        'criterion': 'qualified program in every actual repetition of every included condition',
        'baseline': intersection(baseline_rows, task_ids),
        'previous_all_models': intersection(rows + old_rows, task_ids),
        'replacement': intersection(combined, task_ids),
        'conditions': {c: intersection(rs, task_ids) for c, rs in grouped.items()},
        'jobs': combined, 'new_model_requests': 0, 'program_executions': 0,
        'note': 'Qualification is not test correctness. Pending tasks are not failures. Live snapshots are provisional.',
        'source_plans': {'new': sha(folder / 'study.json'), 'reference': sha(old_folder / 'study.json')},
        'analysis_code_sha256': sha(Path(__file__))}
    out = new_run(root, 'cohort', output)
    write(out / 'cohort.json', result)
    state = result['replacement']
    text = (f"Qualified common tasks: {state['confirmed_count']} confirmed, at most {state['possible_count']} possible, final={state['final']}.\n"
            f"Reused baseline: {result['baseline']['confirmed_count']}. Previous full model comparison: {result['previous_all_models']['confirmed_count']}.\n"
            "No model requests or program execution. Pending qualifications are not counted as failed.\n")
    (out / 'report.txt').write_text(text, encoding='utf-8')
    print(text + str(out))
    return out
