"""Join fixed classical runs and repeated LLM results on explicit task sets."""
from contextlib import redirect_stdout
from io import StringIO
import json
from statistics import mean

from .analysis import csv_write, report
from .io import new_run, read, records, selection, sha, write, task_path
from .study import load
from .study_analysis import report_study, statistics


CLASSICAL = ['synthphonia', 'merlin', 'prose', 'crossbeam', 'bustle']


def complete(scores, repetitions):
    return len(scores) == repetitions and all(x is not None for x in scores)


def aggregate(conditions, values, task_ids):
    metrics = sorted({metric for bymetric in values.values() for metric in bymetric})
    matched, paired = [], []
    names = list(conditions)

    def common(selected, metric):
        available = [set(values[c].get(metric, {})) for c in selected]
        tasks = set.intersection(*available) if available else set()
        return sorted(t for t in tasks if all(complete(values[c][metric][t], conditions[c]['repetitions']) for c in selected))

    for metric in metrics:
        shared = common(names, metric)
        for condition in names:
            info = conditions[condition]
            scores = values[condition].get(metric, {})
            repeat_means = [mean(scores[t][r] for t in shared) for r in range(info['repetitions'])] if shared else []
            stat = statistics(repeat_means)
            matched.append({'condition': condition, **info, 'metric': list(metric),
                'cohort_tasks': len(task_ids), 'applicable_tasks': len(scores),
                'complete_tasks': len(common([condition], metric)), 'common_completed_tasks': len(shared),
                'common_task_ids': shared, 'mean': stat['mean'], 'sample_sd': stat['sample_sd'],
                'repeat_means': repeat_means, 'task_set': 'common_to_all_conditions_and_all_actual_repetitions'})
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                shared_pair = common([first, second], metric)
                left = [mean(values[first][metric][t]) for t in shared_pair]
                right = [mean(values[second][metric][t]) for t in shared_pair]
                differences = [a - b for a, b in zip(left, right)]
                paired.append({'first': first, 'second': second, 'metric': list(metric),
                    'first_repetitions': conditions[first]['repetitions'],
                    'second_repetitions': conditions[second]['repetitions'],
                    'cohort_tasks': len(task_ids), 'common_completed_tasks': len(shared_pair),
                    'common_task_ids': shared_pair, 'first_mean': mean(left) if left else None,
                    'second_mean': mean(right) if right else None,
                    'mean_task_difference': mean(differences) if differences else None,
                    'first_better': sum(x > 0 for x in differences), 'first_worse': sum(x < 0 for x in differences),
                    'ties': sum(x == 0 for x in differences),
                    'interpretation': 'descriptive paired task means over actual repetitions'})
    return matched, paired


def classical_source(root, manifest):
    spec = manifest['config'].get('classical_reference')
    experiment = spec['experiment'] if spec else 'main'
    cfg = selection(root, experiment, ','.join(CLASSICAL))
    folder = root / spec['directory'] if spec else root / 'results/published/main'
    if spec:
        saved = read(folder / 'selection.json')
        for key in ['id', 'version', 'task_ids', 'systems', 'task_set', 'evaluation']:
            if saved.get(key) != cfg.get(key):
                raise ValueError('Fresh classical result selection differs: ' + key)
        cfg = saved
        if read(folder / 'status.json').get('status') != 'completed':
            raise ValueError('Fresh classical evaluation must finish before comparison.')
    return cfg, folder


def evidence_hashes(root, folder, manifest):
    paths = {'study/study.json': folder / 'study.json'}
    for job in manifest['jobs']:
        for phase in ['synthesis', 'evaluation']:
            base = folder / job['directory'] / phase
            for name in ['selection.json', 'programs.json', 'outcomes.json', 'status.json',
                         'predictions.jsonl', 'predictions.jsonl.gz', 'bases.jsonl', 'bases.jsonl.gz',
                         'checkpoint.json', 'provenance.json']:
                path = base / name
                if path.is_file():
                    paths['study/' + path.relative_to(folder).as_posix()] = path
    cfg, classical_folder = classical_source(root, manifest)
    fresh = bool(manifest['config'].get('classical_reference'))
    paths['classical/programs.json'] = classical_folder / 'programs.json' if fresh else root / cfg['programs']
    paths['classical/experiment.json'] = root / 'experiments' / (cfg['id'] + '.json')
    names = ['predictions.jsonl', 'predictions.jsonl.gz', 'bases.jsonl', 'bases.jsonl.gz']
    if fresh:
        names += ['selection.json', 'outcomes.json', 'provenance.json', 'status.json']
    for name in names:
        path = classical_folder / name
        if path.is_file():
            paths['classical/' + name] = path
    return {key: sha(path) for key, path in sorted(paths.items())}


def report_combined(root, source, output=None):
    folder, manifest = load(root, source, execution=False)
    classical, classical_folder = classical_source(root, manifest)
    cfg = manifest['config']
    if cfg.get('classical_reference'):
        actual = {tid: sha(task_path(root, classical, tid)) for tid in classical['task_ids']}
        if actual != manifest['task_hashes']:
            raise ValueError('Classical and LLM behavioral task sets differ.')
    for key in ['task_ids', 'evaluation', 'examples_per_task']:
        if classical.get(key) != cfg.get(key):
            raise ValueError('Classical and study inputs differ: ' + key)
    from .replacement import reference
    ref = reference(root, manifest)
    sources = [('study', folder, manifest, None)]
    if ref:
        sources.append(('reference', *ref))
    def source_hashes():
        return {label + '/' + k: v for label, location, plan, _ in sources
                for k, v in evidence_hashes(root, location, plan).items()}
    initial = source_hashes()
    out = new_run(root, 'comparison', output)
    with redirect_stdout(StringIO()):
        report(root, classical, source=classical_folder, output=out / 'classical')
        for label, location, plan, slots in sources:
            report_study(root, location, output=out / label, model_slots=slots)
    conditions, values = {}, {}
    for system in CLASSICAL:
        name = 'classical/' + system
        conditions[name] = {'system': system, 'family': 'symbolic DSL synthesis' if system in CLASSICAL[:3] else 'neural-guided search',
            'model_slot': None, 'model': None, 'repetitions': 1, 'analysis': 'fresh_synthesis' if cfg.get('classical_reference') else 'historical_fixed_program', 'source_study_id': None, 'source_experiment': classical['id']}
        values[name] = {}
    for label, location, plan, slots in sources:
        for row in read(out / label / 'metrics.json'):
            name = row['condition']
            if name in conditions and conditions[name].get('source_study_id') != plan['study_id']:
                raise ValueError('Duplicate comparison condition across different studies.')
            conditions[name] = {k: row[k] for k in ['system', 'family', 'model_slot', 'model', 'repetitions']}
            conditions[name].update(analysis='original_study_responses', source_study_id=plan['study_id'], source_experiment=plan['experiment'])
            values.setdefault(name, {})
    for row in read(out / 'classical/task_metrics.json'):
        name, metric = 'classical/' + row['system'], ('suite', row['suite'])
        values[name].setdefault(metric, {})[row['task_id']] = [row['accuracy'] if row['complete'] else None]
    for row in records(out / 'classical/profile_tasks.jsonl'):
        name = 'classical/' + row['system']
        metric = ('profile', *(row[k] for k in ['dimension', 'regime_family', 'regime', 'expectation']))
        values[name].setdefault(metric, {})[row['task_id']] = [row['accuracy'] if row['complete'] else None]
    for label, _, _, _ in sources:
        for row in read(out / label / 'task_stability.json'):
            name, metric = row['condition'], tuple(row['metric'])
            values[name].setdefault(metric, {})[row['task_id']] = row['accuracies']
    metrics, paired = aggregate(conditions, values, cfg['task_ids'])
    availability = []
    for row in read(out / 'classical/coverage.json')['systems']:
        availability.append({'condition': 'classical/' + row['system'], 'repeat': 1, 'run_present': True, 'source_study_id': None,
            'tasks': len(cfg['task_ids']), 'programs': row['synthesis']['programs'],
            'synthesis_statuses': row['synthesis']['statuses'], **row['checks']})
    for label, _, plan, _ in sources:
        availability += [{**row, 'source_study_id': plan['study_id']} for row in read(out / label / 'availability.json')]
    task_scores = [{'condition': c, 'metric': list(m), 'task_id': t, 'repetitions': conditions[c]['repetitions'],
                    'accuracies': scores, 'complete': complete(scores, conditions[c]['repetitions'])}
                   for c, bymetric in values.items() for m, bytask in sorted(bymetric.items()) for t, scores in sorted(bytask.items())]
    for name, rows in [('metrics', metrics), ('paired', paired), ('availability', availability), ('task_scores', task_scores)]:
        write(out / (name + '.json'), rows)
        csv_write(out / (name + '.csv'), [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                                        for k, v in row.items()} for row in rows])
    if source_hashes() != initial:
        raise ValueError('Source evidence changed during comparison.')
    write(out / 'manifest.json', {'schema_version': 1, 'analysis': 'classical_and_repeated_study',
        'source_experiment': cfg['id'], 'source_study_id': manifest['study_id'], 'source_plan_digest': manifest['plan_digest'],
        'comparison_reference': cfg.get('comparison_reference'),
        'classical_experiment': classical['id'], 'classical_version': classical['version'],
        'task_ids': cfg['task_ids'], 'task_hashes': manifest['task_hashes'], 'conditions': conditions,
        'source_files': initial, 'unit_of_analysis': 'task',
        'analysis_code_hashes': {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / 'src').rglob('*.py'))},
        'new_model_requests': 0, 'synthesis_calls': 0, 'program_executions': 0,
        'excluded': ['historical Direct Python/Sol', 'post-hoc Direct Python format reanalysis'] + cfg.get('comparison_reference', {}).get('replaced_model_slots', []),
        'aggregation': {'metrics': 'same tasks across every condition and actual repetition',
                        'paired': 'same tasks across each pair and all their actual repetitions',
                        'classical': 'one observation per task, no duplicated repetitions',
                        'missing': 'undefined, never replaced by zero',
                        'uncertainty': 'sample SD of repeat means, absent for a single run'}})
    text = (f"Comparison: {len(conditions)} conditions on {len(cfg['task_ids'])} tasks.\n"
            "Five fixed classical runs and the selected repeated LLM conditions.\n"
            "metrics.csv uses one common task set per metric across all conditions and repetitions.\n"
            "paired.csv uses an explicit common task set for each pair.\n"
            "Always report availability and task counts alongside conditional accuracy.\n"
            "Classical runs are not copied into five artificial repetitions.\n"
            "Historical Sol and the post-hoc format reanalysis are excluded.\n"
            "No model requests, synthesis or program execution.\n")
    (out / 'report.txt').write_text(text, encoding='utf-8')
    print(text + str(out))
    return out
