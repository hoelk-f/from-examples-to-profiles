"""Report extension cases separately from their original evidence."""
from collections import defaultdict
import json
from statistics import mean
from .analysis import csv_write
from .assessment import assess, task_metric
from .comparison import aggregate
from .extension import load, verify_replay
from .io import new_run, read, records, sha, tasks_for, write
from .study_analysis import statistics


def report_extension(root, source, output=None):
    folder, manifest = load(root, source, execution=False)
    task_ids = manifest['config']['task_ids']
    conditions, values, availability, replay, additional = {}, {}, [], [], []
    input_hashes = {}
    for job in manifest['jobs']:
        condition, rep = job['condition'], job['repeat']
        target = folder / job['directory'] / 'evaluation'
        if not (target / 'status.json').exists() or read(target / 'status.json')['status'] != 'completed':
            raise ValueError('Complete the extension jobs before producing its final report.')
        replay.append(verify_replay(root, folder, job))
        for name in ['selection.json', 'programs.json', 'outcomes.json', 'predictions.jsonl', 'bases.jsonl', 'replay-verification.json']:
            input_hashes[str((target / name).relative_to(folder))] = sha(target / name)
        cfg = read(target / 'selection.json')
        if cfg != job['config']:
            raise ValueError('Extension report job identity changed.')
        nrepeat = sum(j['condition'] == condition for j in manifest['jobs'])
        conditions.setdefault(condition, {**{k: job[k] for k in ['system', 'family', 'model_slot', 'model']},
                                         'repetitions': nrepeat, 'analysis': 'frozen_program_behavioral_extension'})
        values.setdefault(condition, {})
        programs = read(target / 'programs.json')
        result = assess(root, cfg, list(records(target / 'predictions.jsonl')), list(records(target / 'bases.jsonl')),
                        programs, read(target / 'outcomes.json'))
        system = result['systems'][0]
        availability.append({'condition': condition, 'repeat': rep, 'programs': system['synthesis']['programs'],
            'tasks': len(task_ids), **system['checks'], 'obligations': system['obligations']})
        bymetric = defaultdict(lambda: defaultdict(dict))
        for row in result['task_rows']:
            metric = ('suite', row['suite'])
            scores = values[condition].setdefault(metric, {}).setdefault(row['task_id'], [None] * nrepeat)
            scores[rep - 1] = row['accuracy']
        for row in result['assertions']:
            if row['suite'] != 'behavioral':
                continue
            metrics = [('operator', row['operator'], row['expectation'])]
            for key in ['side', 'offset', 'expected_output_change']:
                if key in row['parameter']:
                    metrics.append(('parameter', row['operator'], key, str(row['parameter'][key]), row['expectation']))
            for cell in row['profile_cells']:
                metrics.append(('profile', *cell))
            for metric in metrics:
                bymetric[metric][row['task_id']][row['check_id']] = row['status']
        for metric, bytask in bymetric.items():
            for tid, checks in bytask.items():
                scores = values[condition].setdefault(metric, {}).setdefault(tid, [None] * nrepeat)
                scores[rep - 1] = task_metric(checks.values())['accuracy']
        present = {r['task_id'] for r in programs.values()}
        original = defaultdict(list)
        for row in records(root / job['observations']['predictions']):
            if row['system'] == job['system'] and row['task_id'] in present and row['suite'] == 'behavioral':
                original[row['task_id']].append(row['status'] == 'returned' and isinstance(row.get('actual'), str) and row['actual'] == row['expected'])
        old_pass, new_fail = [], []
        for tid, verdicts in original.items():
            scores = values[condition].setdefault(('suite', 'original_behavioral'), {}).setdefault(tid, [None] * nrepeat)
            scores[rep - 1] = mean(verdicts)
            if all(verdicts):
                old_pass.append(tid)
                score = values[condition].get(('suite', 'behavioral'), {}).get(tid, [None] * nrepeat)[rep - 1]
                if score is not None and score < 1:
                    new_fail.append(tid)
        additional.append({'condition': condition, 'repeat': rep, 'available_tasks': len(present),
            'original_behavioral_all_pass_tasks': len(old_pass), 'new_failure_tasks': len(new_fail),
            'fraction': len(new_fail) / len(old_pass) if old_pass else None, 'task_ids': sorted(new_fail)})
    metrics, paired = aggregate(conditions, values, task_ids)
    conditional, task_rows, balanced = [], [], []
    for condition, bymetric in values.items():
        n = conditions[condition]['repetitions']
        for metric, bytask in sorted(bymetric.items()):
            common = sorted(t for t, scores in bytask.items() if len(scores) == n and all(x is not None for x in scores))
            means = [mean(bytask[t][r] for t in common) for r in range(n)] if common else []
            conditional.append({'condition': condition, 'metric': list(metric), 'tasks': len(common),
                'task_ids': common, **statistics(means), 'repeat_means': means,
                'task_set': 'own_condition_complete_in_all_original_repetitions'})
            for tid, scores in sorted(bytask.items()):
                task_rows.append({'condition': condition, 'metric': list(metric), 'task_id': tid, 'accuracies': scores})
    families = defaultdict(list)
    for metric in {m for c in values.values() for m in c}:
        if metric[0] == 'parameter':
            families[metric[1], metric[2], metric[-1]].append(metric)
    groups = {'all_conditions': list(conditions)}
    for model in sorted({c['model_slot'] for c in conditions.values() if c['model_slot']}):
        groups['methods/' + model] = [c for c, info in conditions.items() if info['model_slot'] == model]
    groups['classical'] = [c for c in conditions if c.startswith('classical/')]
    for group, members in groups.items():
        for family, ms in sorted(families.items()):
            common = set(task_ids)
            for cond in members:
                for metric in ms:
                    common &= {t for t, xs in values[cond].get(metric, {}).items()
                               if len(xs) == conditions[cond]['repetitions'] and all(x is not None for x in xs)}
            for cond in members:
                for metric in sorted(ms):
                    means = [mean(values[cond][metric][t][r] for t in sorted(common)) for r in range(conditions[cond]['repetitions'])] if common else []
                    balanced.append({'group': group, 'condition': cond, 'metric': list(metric),
                        'tasks': len(common), 'task_ids': sorted(common), **statistics(means), 'repeat_means': means,
                        'task_set': 'fixed_across_selected_conditions_repetitions_and_parameter_levels'})
    out = new_run(root, 'extension-report', output)
    for name, rows in [('metrics', metrics), ('paired', paired), ('conditional', conditional),
                       ('parameter_comparisons', balanced), ('availability', availability), ('task_scores', task_rows),
                       ('additional_failures', additional), ('replay', replay)]:
        write(out / (name + '.json'), rows)
        csv_write(out / (name + '.csv'), [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()} for r in rows])
    for name, expected in input_hashes.items():
        if sha(folder / name) != expected:
            raise ValueError('Extension evidence changed during reporting.')
    load(root, folder, execution=False)
    summary = {'experiment': manifest['experiment'], 'version': manifest['version'],
        'extension_id': manifest['extension_id'], 'jobs': len(manifest['jobs']), 'conditions': conditions,
        'task_count': len(task_ids), 'generation': read(folder / 'generation.json'),
        'heldout_outputs_identical': sum(r['heldout_outputs_identical'] for r in replay),
        'base_outputs_identical': sum(r['base_outputs_identical'] for r in replay),
        'available_programs': sum(r['programs'] for r in replay), 'new_model_requests': 0, 'synthesis_calls': 0,
        'unit_of_analysis': 'task', 'uncertainty': 'sample SD across actual repetition means',
        'scope': 'exploratory additional suite, original suite remains separate',
        'source_plan_sha256': sha(folder / 'extension.json'), 'evidence_hashes': input_hashes,
        'analysis_code_hashes': {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / 'src').rglob('*.py'))}}
    write(out / 'summary.json', summary)
    lines = [f"Extension {manifest['experiment']}: {len(manifest['jobs'])} completed jobs, {summary['available_programs']} frozen programs.",
        f"{summary['generation']['case_count']} additional behavioral inputs on {len(task_ids)} tasks.",
        f"All {summary['heldout_outputs_identical']} held-out outputs and {summary['base_outputs_identical']} base outputs match the originals.",
        'No new synthesis or model requests. Original results remain a separate suite.',
        'Metrics use equal task weights and explicit common task sets. Missing programs have no verdict.',
        'Parameter comparisons additionally hold the task set fixed across parameter levels.']
    (out / 'report.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines) + '\n' + str(out))
    return out
