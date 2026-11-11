"""Descriptive within-operator comparisons on the existing tests."""
from collections import defaultdict
from fractions import Fraction
from itertools import combinations
import json

from pbe.scoring import assertion_key, cells, score
from .common import ORDER, OPS, cases, passed, table, write


def operator_profiles(out, data):
    local, unique, sides, expectations, outcomes = {}, {}, {}, {}, {}
    profile_rows = []
    by_task = defaultdict(list)
    for key, program in data['records'].items():
        c, r, tid = key
        pid = program['id']
        by_task[tid].append(key)
        bases = {x['case_id']: dict(data['observations'][pid, 'training', x['case_id']], expected=x['expected'])
                 for x in cases('main', tid) if x['suite'] == 'training'}
        buckets, unique_buckets, side_buckets, expectation_buckets, raw = (defaultdict(dict) for _ in range(5))
        for ob in data['tasks'][tid]['behavioral']['obligations']:
            if ob['status'] != 'planned':
                continue
            op, cid = ob['operator_id'], ob['case_id']
            variant = data['observations'][pid, 'behavioral', cid]
            exact = next(a['expected_output'] for a in ob['assertions'] if a['expectation'] == 'Exact Output')
            raw[op][cid] = passed(variant, exact)
            side = ob['parameter']['side'] if op == 'S01' else 'all'
            side_buckets[op, side][cid] = raw[op][cid]
            for assertion in ob['assertions']:
                verdict = score(assertion, variant, bases.get(assertion.get('base_id')))
                identity = assertion_key(ob, assertion)
                expectation_buckets[op, assertion['expectation']][identity] = verdict
                for cell in cells(ob, assertion):
                    bucket = buckets[op, cell]
                    if identity in bucket and bucket[identity] != verdict:
                        raise ValueError('Conflicting operator-local assertion.')
                    bucket[identity] = verdict
                    single = unique_buckets[op, cell]
                    if cid in single and single[cid] != verdict:
                        raise ValueError('Conflicting checks for the unique-input control.')
                    single[cid] = verdict
        counts = lambda groups: {k: (sum(v.values()), len(v)) for k, v in groups.items()}
        local[key], unique[key], sides[key], expectations[key] = map(counts, [buckets, unique_buckets, side_buckets, expectation_buckets])
        outcomes[key] = raw
        for (op, cell), (ok, total) in local[key].items():
            profile_rows.append(dict(condition=c, repeat=r, task_id=tid, operator=op,
                dimension=cell[0], regime_family=cell[1], regime=cell[2], expectation=cell[3],
                passed=ok, total=total, accuracy=ok/total))
    table(out/'operator_local_profiles.csv', profile_rows)

    def changed(groups, a, b, op, exact_only=False):
        if groups[a].keys() != groups[b].keys():
            raise ValueError('Programs have different local test definitions.')
        return [k for k in groups[a] if k[0] == op
                and (not exact_only or k[1][-1] == 'Exact Output')
                and Fraction(*groups[a][k]) != Fraction(*groups[b][k])]

    flags = ['comparable', 'equal_rate', 'different_profile', 'different_exact_profile',
             'different_unique_input_profile', 'different_input_outcomes',
             'equal_all_operators_different_profile', 'equal_sides_different_profile',
             'equal_expectations_different_profile']
    counts, pair_rows, witnesses = [], [], {}
    for mode in ['full_holdout', 'first_repeat', 'classical_only', 'all_eligible']:
        for op in OPS:
            task_sets = {flag: set() for flag in flags}
            pair_counts = dict.fromkeys(flags, 0)
            for tid, keys in by_task.items():
                eligible = [k for k in keys if
                    (mode == 'all_eligible' or data['metrics'][*k, 'heldout'] == 1)
                    and (mode != 'first_repeat' or k[1] == 1)
                    and (mode != 'classical_only' or k[0] in ORDER[:5])]
                for a, b in combinations(eligible, 2):
                    if a[0] == b[0] or op not in data['operators'][a] or op not in data['operators'][b]:
                        continue
                    equal = data['operators'][a][op] == data['operators'][b][op]
                    different = changed(local, a, b, op) if equal else []
                    values = dict(comparable=True, equal_rate=equal, different_profile=bool(different),
                        different_exact_profile=equal and bool(changed(local, a, b, op, exact_only=True)),
                        different_unique_input_profile=equal and bool(changed(unique, a, b, op)),
                        different_input_outcomes=equal and outcomes[a][op] != outcomes[b][op],
                        equal_all_operators_different_profile=bool(different) and data['operators'][a] == data['operators'][b],
                        equal_sides_different_profile=bool(different) and not changed(sides, a, b, op),
                        equal_expectations_different_profile=bool(different) and not changed(expectations, a, b, op))
                    for flag, value in values.items():
                        if value:
                            task_sets[flag].add(tid)
                            pair_counts[flag] += 1
                    if different:
                        details = [dict(cell=k[1], a=local[a][k], b=local[b][k]) for k in different]
                        pair_rows.append(dict(mode=mode, task_id=tid, operator=op,
                            condition_a=a[0], repeat_a=a[1], condition_b=b[0], repeat_b=b[1],
                            operator_rate=str(data['operators'][a][op]),
                            cells=json.dumps(details, separators=(',', ':'))))
                        if mode == 'full_holdout':
                            for key in [a, b]:
                                for cid in outcomes[key][op]:
                                    witnesses[key, op, cid] = data['observations'][data['records'][key]['id'], 'behavioral', cid]
            counts.append(dict(mode=mode, operator=op,
                **{flag+'_tasks': len(task_sets[flag]) for flag in flags},
                **{flag+'_pairs': pair_counts[flag] for flag in flags},
                different_task_ids='|'.join(sorted(task_sets['different_profile']))))
    table(out/'operator_profile_counts.csv', counts)
    table(out/'operator_profile_pairs.csv', pair_rows)
    witness_rows = []
    for ((c, r, tid), op, cid), observed in witnesses.items():
        case = next(x for x in data['tasks'][tid]['behavioral']['cases'] if x['case_id'] == cid)
        witness_rows.append(dict(condition=c, repeat=r, task_id=tid, operator=op, case_id=cid,
            input=case['input'], expected=case['expected_output'], status=observed['status'], actual=observed['actual']))
    table(out/'operator_profile_examples.csv', witness_rows)
    write(out/'operator_profile_method.json', dict(
        primary='Different conditions, same task, both fully passing holdout, equal exact operator pass rates.',
        grouping='Restrict obligations to one operator before grouping and deduplicating assertions.',
        unit='Distinct tasks per operator. Pairs and overlapping cells are not independent observations.',
        controls=['First repetition', 'Classical only', 'All eligible programs', 'Exact-output cells',
                  'Unique inputs per cell', 'All operator rates equal', 'Insertion side', 'Expectation groups'],
        interpretation='Descriptive differences on the fixed tests, not evidence of general taxonomy superiority.'))
    print('Local operator/profile comparisons and controls computed.', flush=True)
