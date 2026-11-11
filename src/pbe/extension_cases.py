"""Deterministic additions to the frozen field-extraction test suite."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from . import contract
from . import reference_check
from .behavioral import markers, mutable_runs, occurrences, prefix_length, same_skeleton, structure_template, short_hash


OPERATORS = {'S02': ('S01', 'Structure'), 'V06': ('V03', 'Value'), 'V07': ('V04', 'Value')}


def oracle(text, selector):
    answers = []
    for fn, invalid in [(contract.extract, contract.OutsideContract), (reference_check.evaluate, reference_check.Invalid)]:
        try:
            answers.append(fn(text, selector))
        except invalid:
            answers.append(None)
    if answers[0] != answers[1]:
        raise ValueError('Extension reference implementations disagree.')
    return answers[0]


def characters(sample, length, key):
    raw = hashlib.shake_256(json.dumps(key, sort_keys=True, ensure_ascii=True).encode()).digest(length)
    answer = []
    for i, byte in enumerate(raw):
        char = sample[i % len(sample)]
        alphabet = '0123456789' if char.isdigit() else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if char.isupper() else 'abcdefghijklmnopqrstuvwxyz'
        answer.append(alphabet[byte % len(alphabet)])
    return ''.join(answer)


def insertion_points(text, selector, span, template):
    if not template:
        return {}
    if template['kind'] == 'delimiter_field':
        boundaries = [start for start, _ in contract.tokens(text, template['marker']) if 0 < start < len(text)]
        before = [p for p in boundaries if p <= span[0]]
        after = [p for p in boundaries if p >= span[1]]
        points = {'before': max(before) if before else None, 'after': min(after) if after else None}
    else:
        opening, closing = template['marker'], template['closing_marker']
        start = text.rfind(opening) if selector[0][0] == 'after_last' else text.find(opening)
        end = text.find(closing, start + len(opening))
        if start < 0 or end < 0 or not start + len(opening) <= span[0] <= span[1] <= end:
            return {}
        points = {'before': start, 'after': end + len(closing)}
    protected = occurrences(text, markers(selector))
    return {side: point for side, point in points.items() if point is not None and 0 < point < len(text)
            and not any(a < point < b for a, b, _ in protected)}


def generate_task(task, design):
    selector = task['parameters']['selector']
    literals = markers(selector)
    bases = deepcopy(task['behavioral']['bases'])
    if len(bases) != 2:
        raise ValueError('Extension version 1 requires the two fixed synthesis examples.')
    for example in task['examples']:
        result = oracle(example['input'][0], selector)
        if result is None or result[0] != example['output']:
            raise ValueError('Source example disagrees with the contract.')
    spans = []
    for base in bases:
        result = oracle(base['input'], selector)
        if result is None or result[0] != base['expected_output']:
            raise ValueError('Fixed synthesis example disagrees with the contract.')
        spans.append(result[1])
    ranges = {'V06': [prefix_length(b['input'], s, literals) for b, s in zip(bases, spans)],
              'V07': [len(b['expected_output']) for b in bases]}
    template = structure_template(selector)
    old_structure = any(ob['operator_id'] == 'S01' and ob['status'] == 'planned' for ob in task['behavioral']['obligations'])
    forbidden = {e['input'][0] for e in task['examples']} | {c['input'] for c in task['behavioral']['cases']}
    generated, obligations = {}, []
    for bi, (base, span) in enumerate(zip(bases, spans)):
        text, answer = base['input'], base['expected_output']
        runs = mutable_runs(text, literals)
        points = insertion_points(text, selector, span, template) if old_structure else {}
        for op, (original_op, dimension) in OPERATORS.items():
            if op == 'S02':
                parameters = [{'side': side, 'variant': v} for side in ['before', 'after'] for v in range(1, design['variants'] + 1)]
            else:
                maximum = max(ranges[op])
                parameters = [{'offset': offset, 'observed_max': maximum, 'desired_length': maximum + offset, 'variant': v}
                              for offset in design['length_offsets'] for v in range(1, design['variants'] + 1)]
            for pi, parameter in enumerate(parameters, 1):
                oid = f"{base['base_id']}-E1-{op}-{pi}"
                row = {'obligation_id': oid, 'task_id': task['task_id'], 'base_id': base['base_id'],
                       'operator_id': op, 'source_operator': original_op, 'dimension': dimension,
                       'parameter': dict(parameter), 'requirement_scope': 'study_defined_literal_contract'}
                obligations.append(row)
                reason, choices = None, []
                if op == 'S02':
                    if not old_structure or not template:
                        reason = 'source_structure_template_not_covered'
                    elif parameter['side'] not in points:
                        reason = 'no_strictly_internal_adjacent_boundary'
                else:
                    current = prefix_length(text, span, literals) if op == 'V06' else len(answer)
                    target = parameter['desired_length']
                    delta = target - current
                    choices = [(a, b) for a, b in runs if (b <= span[0] if op == 'V06' else span[0] <= a < b <= span[1])]
                    if target < (0 if op == 'V06' else 1):
                        reason = 'requested_length_outside_contract'
                    elif delta == 0:
                        reason = 'requested_length_already_present'
                    elif not choices:
                        reason = 'no_unprotected_ascii_run_in_required_region'
                    elif all(b - a + delta < 0 for a, b in choices):
                        reason = 'requested_length_cannot_be_realized_by_one_run'
                if reason:
                    row.update(status='not_applicable_to_operator', reason=reason)
                    continue
                rejected = Counter()
                for trial in range(design['maximum_attempts']):
                    key = [design['seed'], task['generation_seed'], op, bi, parameter, trial]
                    relation, expected, expected_span = None, None, None
                    if op == 'S02':
                        sample = next((c for c in answer if c.isascii() and c.isalnum()), 'a')
                        dummy = characters(sample, max(3, min(12, len(answer))), key)
                        if any(marker in dummy for marker in literals) or dummy == answer:
                            rejected['dummy_conflicts_with_marker_or_target'] += 1
                            continue
                        point = points[parameter['side']]
                        insert = (template['marker'] + dummy + template['closing_marker']
                                  if template['kind'] == 'marked_block' else dummy + template['marker'])
                        altered = text[:point] + insert + text[point:]
                        edit = {'position': point, 'inserted': insert, 'template': template, 'dummy_field': dummy}
                    else:
                        a, b = choices[trial % len(choices)]
                        width = b - a + delta
                        if width < 0:
                            rejected['mutable_run_too_short'] += 1
                            continue
                        replacement = text[a:b] + characters(text[b - 1], delta, key) if delta > 0 else characters(text[a:b], width, key)
                        altered = text[:a] + replacement + text[b:]
                        edit = {'start': a, 'end': b, 'replacement': replacement}
                        if not same_skeleton(text, altered, literals):
                            rejected['protected_structure_changed'] += 1
                            continue
                        if op == 'V06':
                            expected, expected_span = answer, (span[0] + delta, span[1] + delta)
                            relation = {'expectation': 'Invariance', 'operation': 'identity'}
                        else:
                            start, end = a - span[0], b - span[0]
                            expected, expected_span = answer[:start] + replacement + answer[end:], (span[0], span[1] + delta)
                            relation = {'expectation': 'Equivariance', 'operation': 'replace_slice', 'start': start, 'end': end, 'replacement': replacement}
                    if altered == text or altered in forbidden:
                        rejected['overlap_with_source_or_original_behavioral_suite'] += 1
                        continue
                    if len(altered) > design['maximum_input_length']:
                        rejected['input_length_cap'] += 1
                        continue
                    result = oracle(altered, selector)
                    if result is None:
                        rejected['outside_contract'] += 1
                        continue
                    if expected is not None and result != (expected, expected_span):
                        rejected['operator_postcondition_not_met'] += 1
                        continue
                    expected, expected_span = result
                    regime = {'contract_conformance': {'value': 'Valid'}, 'construction_intent': {'value': 'Targeted'},
                              'distribution_membership': {'status': 'unclear', 'reason': 'no_sampling_distribution_defined'},
                              'partition_location': {'status': 'unselected'}}
                    if op == 'S02':
                        if expected == answer:
                            relation = {'expectation': 'Invariance', 'operation': 'identity'}
                        lower, upper = min(len(occurrences(b['input'], [template['marker']])) for b in bases), max(len(occurrences(b['input'], [template['marker']])) for b in bases)
                        value = len(occurrences(altered, [template['marker']]))
                        attribute = 'marker_occurrences'
                        row['parameter']['expected_output_change'] = 'unchanged' if expected == answer else 'changed'
                        row['parameter']['insertion_position'] = point
                    else:
                        lower, upper = min(ranges[op]), max(ranges[op])
                        value = prefix_length(altered, expected_span, literals) if op == 'V06' else len(expected)
                        attribute = 'prefix_length_before_left_boundary' if op == 'V06' else 'target_length'
                        if value != parameter['desired_length']:
                            rejected['requested_length_not_reached'] += 1
                            continue
                    regime['observed_range_position'] = {'attribute': attribute,
                        'value': 'Interpolation' if lower <= value <= upper else 'Extrapolation',
                        'observed_min': lower, 'observed_max': upper, 'test_value': value, 'reference': 'two_synthesis_examples'}
                    cid = task['task_id'] + '-E1-C' + short_hash(altered)
                    case = {'task_id': task['task_id'], 'case_id': cid, 'input': altered,
                            'expected_output': expected, 'expected_span': list(expected_span),
                            'requirement_scope': 'study_defined_literal_contract', 'obligation_ids': []}
                    prior = generated.setdefault(cid, case)
                    if any(prior[k] != case[k] for k in ['input', 'expected_output', 'expected_span']):
                        raise ValueError('Conflicting extension test identity.')
                    prior['obligation_ids'].append(oid)
                    assertions = [{'assertion_id': oid + '-exact', 'expectation': 'Exact Output', 'expected_output': expected}]
                    if relation:
                        assertions.append({'assertion_id': oid + '-relation', 'base_id': base['base_id'], **relation})
                    row.update(status='planned', case_id=cid, assertions=assertions, regime=regime,
                               input_edit=edit, successful_trial=trial, rejected_proposals=dict(rejected))
                    break
                else:
                    row.update(status='unresolved', reason='no_fresh_valid_variant_within_budget',
                               rejected_proposals=dict(rejected), attempts=design['maximum_attempts'])
    applicability = []
    for op in OPERATORS:
        rows = [r for r in obligations if r['operator_id'] == op]
        applicability.append({'task_id': task['task_id'], 'operator_id': op, 'obligations': len(rows),
            'statuses': dict(Counter(r['status'] for r in rows)),
            'unique_cases': len({r['case_id'] for r in rows if r['status'] == 'planned'}),
            'reasons': dict(Counter(r['reason'] for r in rows if 'reason' in r))})
    result = deepcopy(task)
    result['behavioral'] = {'bases': bases, 'cases': list(generated.values()), 'obligations': obligations, 'applicability': applicability}
    result['extension'] = {'version': 1, 'seed': design['seed'], 'source_family': task['family_id'],
                           'scope': 'additional_behavioral_cases_with_original_heldout_controls'}
    return result
