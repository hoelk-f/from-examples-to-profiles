"""Descriptive repeat statistics with tasks as the unit of analysis."""
from collections import defaultdict
from statistics import mean, stdev
import json
from .assessment import assess
from .io import new_run, read, records, verified_program, write, sha
from .study import job_config, load


def statistics(values):
    return {'n': len(values), 'mean': mean(values) if values else None,
            'sample_sd': stdev(values) if len(values) > 1 else None}


def observations(folder, name):
    path = next((folder / n for n in [name + '.jsonl.gz', name + '.jsonl'] if (folder / n).exists()), None)
    return list(records(path)) if path else []


def report_study(root, source, output=None, *, model_slots=None):
    from .analysis import csv_write
    folder, manifest = load(root, source, execution=False)
    if model_slots is not None and (not model_slots or not set(model_slots) <= set(manifest['config']['study']['model_slots'])):
        raise ValueError('Unknown or empty study report model selection.')
    jobs = [j for j in manifest['jobs'] if model_slots is None or j['model_slot'] in model_slots]
    repetitions = manifest['config']['study']['repetitions']
    task_ids = manifest['config']['task_ids']
    conditions = {}
    values = defaultdict(lambda: defaultdict(dict))
    availability, failures = [], {}
    run_ids = set()
    for job in jobs:
        condition, repeat = job['condition'], job['repeat']
        conditions[condition] = {k: job[k] for k in ['system', 'family', 'model_slot', 'model']}
        cfg = job_config(manifest, job)
        target = folder / job['directory']
        evaluation, synthesis = target / 'evaluation', target / 'synthesis'
        evidence = evaluation if evaluation.exists() else synthesis
        if evidence.exists():
            saved = read(evidence / 'selection.json')
            if saved.get('study_run') != cfg['study_run'] or saved['task_ids'] != task_ids or saved['evaluation'] != cfg['evaluation']:
                raise ValueError('Saved run does not match its study job: ' + str(evidence))
            run_id = saved.get('run_id')
            if not run_id or run_id in run_ids:
                raise ValueError('Missing or reused synthesis run identity.')
            run_ids.add(run_id)
            cfg = saved
        programs = read(evidence / 'programs.json') if (evidence / 'programs.json').exists() else {}
        for record in programs.values():
            if record.get('study_run') != cfg['study_run'] or record.get('run_id') != cfg.get('run_id'):
                raise ValueError('Program belongs to another condition or repetition.')
            verified_program(root, record, evidence / 'programs.json')
        outcomes = read(evidence / 'outcomes.json') if (evidence / 'outcomes.json').exists() else []
        predictions, bases = observations(evidence, 'predictions'), observations(evidence, 'bases')
        result = assess(root, cfg, predictions, bases, programs, outcomes)
        coverage = result['systems'][0]
        availability.append({'condition': condition, 'repeat': repeat, 'run_present': evidence.exists(),
            'tasks': len(task_ids), 'programs': coverage['synthesis']['programs'],
            'synthesis_statuses': coverage['synthesis']['statuses'], **coverage['checks']})
        for row in result['task_rows']:
            values[condition, ('suite', row['suite'])][row['task_id']][repeat] = row
        for row in result['profile_tasks']:
            cell = tuple(row[k] for k in ['dimension', 'regime_family', 'regime', 'expectation'])
            values[condition, ('profile', *cell)][row['task_id']][repeat] = row
        seen = set()
        for row in result['assertions']:
            key = condition, row['task_id'], row['suite'], row['check_id']
            if key in seen:
                for cell in row['profile_cells']:
                    if cell not in failures[key]['profile_cells']:
                        failures[key]['profile_cells'].append(cell)
                continue
            seen.add(key)
            record = failures.setdefault(key, {'condition': condition, 'task_id': row['task_id'], 'suite': row['suite'],
                'case_id': row['case_id'], 'check_id': row['check_id'], 'expectation': row['expectation'],
                'profile_cells': list(row['profile_cells']), 'failed_repeats': [], 'passed_repeats': [], 'unobserved_repeats': []})
            field = 'failed_repeats' if row['passed'] is False else 'passed_repeats' if row['passed'] is True else 'unobserved_repeats'
            record[field].append(repeat)
    metric_rows, task_stability = [], []
    for (condition, metric), bytask in sorted(values.items()):
        common = sorted(tid for tid, repeats in bytask.items()
                        if len(repeats) == repetitions and all(r['complete'] for r in repeats.values()))
        repeat_means = [mean(bytask[t][r]['accuracy'] for t in common) for r in range(1, repetitions + 1)] if common else []
        stats = statistics(repeat_means)
        full = len(common) == len(bytask) and bool(bytask)
        completed_repeats = sum(all(repeats[r]['complete'] for repeats in bytask.values()) for r in range(1, repetitions + 1))
        metric_rows.append({'condition': condition, **conditions[condition], 'metric': list(metric),
            'cohort_tasks': len(task_ids), 'applicable_tasks': len(bytask), 'repetitions': repetitions,
            'complete_repetitions': completed_repeats, 'common_completed_tasks': len(common), 'common_task_ids': common,
            'mean': stats['mean'] if full else None, 'sample_sd': stats['sample_sd'] if full else None,
            'common_task_mean': stats['mean'], 'common_task_sample_sd': stats['sample_sd'],
            'common_repeat_means': repeat_means})
        for tid, repeats in sorted(bytask.items()):
            scores = [repeats[r]['accuracy'] for r in range(1, repetitions + 1)]
            observed = [x for x in scores if x is not None]
            complete = len(observed) == repetitions
            task_stability.append({'condition': condition, 'metric': list(metric), 'task_id': tid,
                'planned_repetitions': repetitions, 'observed_repetitions': len(observed), 'accuracies': scores,
                'mean': mean(observed) if complete else None,
                'sample_sd': stdev(observed) if complete and len(observed) > 1 else None,
                'stable_accuracy': len(set(observed)) == 1 if complete else None,
                'fully_passing_repetitions': sum(row['fully_passed'] is True for row in repeats.values()),
                'incomplete_repetitions': repetitions - len(observed)})
    paired = []
    condition_list = list(conditions)
    metrics = sorted({metric for _, metric in values})
    for i, first in enumerate(condition_list):
        for second in condition_list[i + 1:]:
            for metric in metrics:
                left, right = values.get((first, metric), {}), values.get((second, metric), {})
                common = sorted(t for t in set(left) & set(right)
                    if all(side[t][r]['complete'] for side in [left, right] for r in range(1, repetitions + 1)))
                differences = [mean(left[t][r]['accuracy'] - right[t][r]['accuracy'] for r in range(1, repetitions + 1)) for t in common]
                paired.append({'first': first, 'second': second, 'metric': list(metric), 'cohort_tasks': len(task_ids),
                    'common_completed_tasks': len(common), 'common_task_ids': common,
                    'mean_task_difference': mean(differences) if differences else None,
                    'first_better': sum(x > 0 for x in differences), 'first_worse': sum(x < 0 for x in differences),
                    'ties': sum(x == 0 for x in differences), 'interpretation': 'descriptive paired task means, no causal family attribution'})
    family_rows = []
    for family in sorted({c['family'] for c in conditions.values()}):
        members = [c for c, meta in conditions.items() if meta['family'] == family]
        for metric in metrics:
            groups = [values[c, metric] for c in members if (c, metric) in values]
            common = sorted(set.intersection(*(set(g) for g in groups))) if groups else []
            common = [t for t in common if all(g[t][r]['complete'] for g in groups for r in range(1, repetitions + 1))]
            task_means = [mean(g[t][r]['accuracy'] for g in groups for r in range(1, repetitions + 1)) for t in common]
            family_rows.append({'family': family, 'conditions': members, 'metric': list(metric),
                'cohort_tasks': len(task_ids), 'common_completed_tasks': len(common), 'common_task_ids': common,
                'common_task_mean': mean(task_means) if task_means else None,
                'interpretation': 'descriptive average across configured models and repetitions, one method per family'})
    recurring = [dict(r, failed_count=len(r['failed_repeats']), observed_count=len(r['failed_repeats']) + len(r['passed_repeats']),
                      planned_repetitions=repetitions, recurring_failure=len(r['failed_repeats']) >= 2)
                 for r in failures.values() if r['failed_repeats']]
    out = new_run(root, 'study-report', output)
    result = {'schema_version': 1, 'study_id': manifest['study_id'], 'experiment': manifest['experiment'],
        'task_count': len(task_ids), 'repetitions': repetitions, 'planned_jobs': len(jobs), 'selected_model_slots': model_slots,
        'present_jobs': sum(r['run_present'] for r in availability), 'new_model_requests': 0,
        'unit_of_analysis': 'task', 'uncertainty': 'sample SD across repeat means, not a confidence interval',
        'missing_data': 'full-cohort means require all planned repetitions, conditional means use explicit fixed common task sets',
        'family_interpretation': 'descriptive, confounded with individual method', 'metrics': metric_rows}
    write(out / 'summary.json', result)
    write(out / 'provenance.json', {'source_plan_sha256': sha(folder / 'study.json'),
        'source_plan_digest': manifest['plan_digest'], 'source_input_hashes': manifest.get('input_hashes', {}),
        'analysis_code_hashes': {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / 'src').rglob('*.py'))},
        'new_model_requests': 0})
    for name, rows in [('metrics', metric_rows), ('availability', availability), ('task_stability', task_stability),
                       ('paired', paired), ('families', family_rows), ('recurring_failures', recurring)]:
        write(out / (name + '.json'), rows)
        csv_write(out / (name + '.csv'), [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()} for row in rows])
    text = (f"Study {manifest['experiment']}: {result['present_jobs']}/{result['planned_jobs']} jobs present.\n"
            f"{len(task_ids)} tasks, {repetitions} repetitions. Tasks remain the unit of analysis.\n"
            "Means and sample SD use the same tasks in every repetition. Missing values remain unknown.\n"
            "Family comparisons are descriptive. They do not isolate the effect of a synthesis family.\n")
    (out / 'report.txt').write_text(text, encoding='utf-8')
    print(text + str(out))
    return out
