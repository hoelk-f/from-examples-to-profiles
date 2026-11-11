from collections import Counter
import hashlib, json, math, re
from . import contract
from .reference_check import evaluate, Invalid, GOLDEN
SEED = 20261005
TRIALS = 128
OPERATORS = {'V01': {'name': 'Replace target content at fixed length', 'capability': 'content_independence', 'dimension': 'Value', 'variants_per_base': 3, 'expectations': ['Exact Output', 'Equivariance']}, 'V02': {'name': 'Replace irrelevant context at fixed length', 'capability': 'content_independence', 'dimension': 'Value', 'variants_per_base': 3, 'expectations': ['Exact Output', 'Invariance']}, 'V03': {'name': 'Extend the prefix before the left boundary', 'capability': 'boundary_and_length_handling', 'dimension': 'Value', 'factors': [1.5, 2, 4], 'expectations': ['Exact Output', 'Invariance']}, 'V04': {'name': 'Extend the selected field', 'capability': 'boundary_and_length_handling', 'dimension': 'Value', 'factors': [1.5, 2, 4], 'expectations': ['Exact Output', 'Equivariance']}, 'V05': {'name': 'Reduce an atomic target to one character', 'capability': 'boundary_and_length_handling', 'dimension': 'Value', 'variants_per_base': 1, 'expectations': ['Exact Output', 'Equivariance']}, 'S01': {'name': 'Insert a competing field or marked block', 'capability': 'occurrence_selection', 'dimension': 'Structure', 'sides': ['before', 'after'], 'variants_per_side_per_base': 2, 'expectations': ['Exact Output', 'Invariance when the reference output is unchanged']}}

def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))

def short_hash(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()[:20]

def markers(selector):
    return sorted({a for op in selector for a in op[1:] if isinstance(a, str) and a})

def occurrences(text, literals):
    return sorted(((m.start(), m.start() + len(lit), lit) for lit in literals for m in re.finditer('(?=' + re.escape(lit) + ')', text)))

def mutable_runs(text, literals):
    protected = set()
    for a, b, _ in occurrences(text, literals):
        protected.update(range(a, b))
    result = []
    for match in re.finditer('[A-Z]+|[a-z]+|[0-9]+', text):
        start = None
        for i in range(match.start(), match.end() + 1):
            allowed = i < match.end() and i not in protected
            if allowed and start is None:
                start = i
            if not allowed and start is not None:
                result.append((start, i))
                start = None
    return sorted(result, key=lambda span: (-(span[1] - span[0]), span[0]))

def prefix_length(text, span, literals):
    left = span[0]
    widths = [b - a for a, b, _ in occurrences(text, literals) if b == left]
    return left - max(widths, default=0)

def same_skeleton(original, altered, literals, fixed_length=False):
    if re.sub('[A-Za-z0-9]', '', original) != re.sub('[A-Za-z0-9]', '', altered):
        return False
    old, new = (occurrences(original, literals), occurrences(altered, literals))
    return old == new if fixed_length else [x[2] for x in old] == [x[2] for x in new]

def mutate_chars(sample, length, key, different=False):
    data = hashlib.shake_256(canonical([SEED, key]).encode()).digest(length)
    out = []
    for i, byte in enumerate(data):
        c = sample[i % len(sample)]
        alphabet = '0123456789' if c.isdigit() else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c.isupper() else 'abcdefghijklmnopqrstuvwxyz'
        options = alphabet.replace(c, '') if different else alphabet
        out.append(options[byte % len(options)])
    return ''.join(out)

def structure_template(selector):
    core = selector[:-1] if selector[-1][0] == 'trim' else selector
    single = {'before', 'after', 'before_last', 'after_last', 'before_inclusive', 'after_inclusive', 'before_last_inclusive', 'token', 'token_span'}
    if len(core) == 1 and core[0][0] in single:
        return {'kind': 'delimiter_field', 'marker': core[0][1]}
    if len(core) == 2 and core[0][0] in ('after', 'after_last') and (core[1][0] == 'before'):
        return {'kind': 'marked_block', 'marker': core[0][1], 'closing_marker': core[1][1]}
    return None

def generate(task_records, *, unique_variants=False):

    def checked(text, selector):
        a = contract.extract(text, selector)
        b = evaluate(text, selector)
        assert a == b, f'Oracle conflict: {selector!r}, {text!r}, {a!r}, {b!r}'
        assert text[a[1][0]:a[1][1]] == a[0] and a[0]
        return a
    golden_records = []
    for text, selector, answer in GOLDEN:
        outcomes = []
        for function, invalid in [(contract.extract, contract.OutsideContract), (evaluate, Invalid)]:
            try:
                result = function(text, selector)[0]
            except invalid:
                result = None
            assert result == answer, f'Golden oracle check failed: {text!r}, {selector!r}'
            outcomes.append(result)
        golden_records.append({'input': text, 'selector': selector, 'expected': answer, 'expected_status': 'outside_contract' if answer is None else 'valid', 'both_references_agree': True})
    tasks = {t['task_id']: t for t in task_records}
    source_checks = 0
    for task in tasks.values():
        for example in task['examples']:
            assert checked(example['input'][0], task['parameters']['selector'])[0] == example['output']
            source_checks += 1
    cases, obligations, bases, applicability = ({}, [], [], [])
    accepted_variants = set()
    for tid, task in tasks.items():
        namespace = f"T{task['generation_seed']:02d}"
        selector = task['parameters']['selector']
        literals = markers(selector)
        examples = task['split']['training']
        assert len(examples) == 2
        seen_source = {e['input'][0] for e in task['examples']}
        spans = [checked(e['input'], selector)[1] for e in examples]
        ranges = {'prefix_length_before_left_boundary': [prefix_length(e['input'], span, literals) for e, span in zip(examples, spans)], 'target_length': [len(e['output']) for e in examples]}
        template = structure_template(selector)
        if template:
            ranges['marker_occurrences'] = [len(occurrences(e['input'], [template['marker']])) for e in examples]
        task_obligations = []
        for bi, (base, span) in enumerate(zip(examples, spans), 1):
            bid = f'{tid}-B{bi}'
            x, y = (base['input'], base['output'])
            left, right = span
            assert checked(x, selector)[0] == y
            bases.append({'base_id': bid, 'task_id': tid, 'input': x, 'expected_output': y, 'expected_span': list(span), 'source_path': f'data/tasks/{tid}.json#split.training', 'source_index': bi - 1, 'role': 'synthesis_example_for_paired_assertions_only'})
            runs = mutable_runs(x, literals)
            inside = [(a, b) for a, b in runs if left <= a < b <= right]
            outside = [(a, b) for a, b in runs if b <= left or a >= right]
            prefix = [(a, b) for a, b in runs if b <= left]
            atomic = bool(re.fullmatch('[A-Za-z0-9]+', y)) and (not any((a < right and b > left for a, b, _ in occurrences(x, literals))))
            for op_id, op in OPERATORS.items():
                if op_id in ('V01', 'V02'):
                    params = [{'variant': v} for v in range(1, 4)]
                elif op_id in ('V03', 'V04'):
                    attr = 'target_length' if op_id == 'V04' else 'prefix_length_before_left_boundary'
                    maximum = max(ranges[attr])
                    params = [{'factor': f, 'desired_length': max(maximum + 1, math.ceil(f * maximum))} for f in op['factors']]
                elif op_id == 'V05':
                    params = [{'desired_length': 1}]
                else:
                    params = [{'side': side, 'variant': v} for side in op['sides'] for v in (1, 2)]
                choices = {'V01': inside, 'V02': outside, 'V03': prefix, 'V04': inside}.get(op_id, [])
                reason = None
                if op_id in ('V01', 'V02', 'V03', 'V04') and (not choices):
                    reason = 'no_unprotected_ascii_alphanumeric_run_in_required_region'
                if op_id == 'V05' and (not atomic):
                    reason = 'one_character_reduction_would_change_protected_markers_or_non_alphanumeric_structure'
                for pi, param in enumerate(params, 1):
                    oid = f'{bid}-{op_id}-{pi}'
                    row = {'obligation_id': oid, 'task_id': tid, 'base_id': bid, 'operator_id': op_id, 'capability': op['capability'], 'dimension': op['dimension'], 'parameter': param, 'requirement_scope': 'study_defined_literal_contract', 'execution_status': 'not_executed'}
                    obligations.append(row)
                    task_obligations.append(row)
                    if op_id == 'S01' and (not template):
                        row.update(status='unselected', reason='composed_selector_not_covered_by_initial_structure_templates')
                        continue
                    if reason:
                        row.update(status='not_applicable_to_operator', reason=reason)
                        continue
                    rejected = Counter()
                    found = False
                    for trial in range(TRIALS):
                        key = [namespace, op_id, bi, param, trial]
                        relation = None
                        expected = None
                        expected_span = None
                        edit = None
                        if op_id == 'S01':
                            sample = next((c for c in y if c.isascii() and c.isalnum()), 'a')
                            dummy = mutate_chars(sample, max(3, min(12, len(y))), key)
                            if any((m in dummy for m in literals)) or dummy == y:
                                rejected['dummy_contains_marker_or_repeats_target'] += 1
                                continue
                            if template['kind'] == 'marked_block':
                                block = template['marker'] + dummy + template['closing_marker']
                                altered = block + x if param['side'] == 'before' else x + block
                            else:
                                altered = dummy + template['marker'] + x if param['side'] == 'before' else x + template['marker'] + dummy
                            edit = {'template': template, 'side': param['side'], 'dummy_field': dummy}
                        else:
                            if op_id == 'V05':
                                a, b = (left, right)
                                replacement = mutate_chars(y[0], 1, key, different=True)
                            else:
                                a, b = choices[trial % len(choices)]
                                if op_id in ('V01', 'V02'):
                                    replacement = mutate_chars(x[a:b], b - a, key, different=True)
                                else:
                                    current_length = len(y) if op_id == 'V04' else prefix_length(x, span, literals)
                                    delta = param['desired_length'] - current_length
                                    assert delta > 0
                                    replacement = x[a:b] + mutate_chars(x[b - 1], delta, key)
                            altered = x[:a] + replacement + x[b:]
                            edit = {'start': a, 'end': b, 'replacement': replacement}
                            delta = len(replacement) - (b - a)
                            if op_id in ('V02', 'V03'):
                                expected = y
                                shift = delta if b <= left else 0
                                expected_span = (left + shift, right + shift)
                                relation = {'expectation': 'Invariance', 'operation': 'identity'}
                            else:
                                output_edit = {'start': a - left, 'end': b - left, 'replacement': replacement}
                                expected = y[:a - left] + replacement + y[b - left:]
                                expected_span = (left, right + delta)
                                relation = {'expectation': 'Equivariance', 'operation': 'replace_slice', **output_edit}
                            if not same_skeleton(x, altered, literals, op_id in ('V01', 'V02')):
                                rejected['value_operator_changed_marker_or_structure'] += 1
                                continue
                        if altered in seen_source or altered == x:
                            rejected['duplicates_original_source_input'] += 1
                            continue
                        if len(altered) > 4096:
                            rejected['generator_length_cap'] += 1
                            continue
                        try:
                            oracle = contract.extract(altered, selector)
                        except contract.OutsideContract:
                            try:
                                evaluate(altered, selector)
                            except Invalid:
                                rejected['outside_study_contract'] += 1
                                continue
                            raise AssertionError('References disagree about validity')
                        assert oracle == evaluate(altered, selector), 'Conflicting reference results'
                        if expected is not None:
                            if oracle != (expected, expected_span):
                                rejected['operator_postcondition_not_met'] += 1
                                continue
                        else:
                            expected, expected_span = oracle
                            if expected == y:
                                relation = {'expectation': 'Invariance', 'operation': 'identity'}
                        variant_key = (tid, bid, op_id, altered)
                        if unique_variants and variant_key in accepted_variants:
                            rejected['duplicate_generated_variant'] += 1
                            continue
                        accepted_variants.add(variant_key)
                        cid = tid + '-C' + short_hash(altered)
                        if cid not in cases:
                            cases[cid] = {'case_id': cid, 'task_id': tid, 'input': altered, 'expected_output': expected, 'expected_span': list(expected_span), 'requirement_scope': 'study_defined_literal_contract', 'obligation_ids': [], 'execution_status': 'not_executed'}
                        assert cases[cid]['input'] == altered and cases[cid]['expected_output'] == expected
                        cases[cid]['obligation_ids'].append(oid)
                        regime = {'contract_conformance': {'value': 'Valid'}, 'construction_intent': {'value': 'Targeted'}, 'distribution_membership': {'status': 'unclear', 'reason': 'no_sampling_distribution_defined'}, 'partition_location': {'status': 'unselected'}, 'observed_range_position': {'status': 'not_applicable', 'reason': 'categorical_content_change_has_no_ordered_attribute'}}
                        if op_id in ('V03', 'V04', 'V05', 'S01'):
                            attr = 'prefix_length_before_left_boundary' if op_id == 'V03' else 'marker_occurrences' if op_id == 'S01' else 'target_length'
                            value = prefix_length(altered, expected_span, literals) if op_id == 'V03' else len(occurrences(altered, [template['marker']])) if op_id == 'S01' else len(expected)
                            lower, upper = (min(ranges[attr]), max(ranges[attr]))
                            regime['observed_range_position'] = {'attribute': attr, 'value': 'Interpolation' if lower <= value <= upper else 'Extrapolation', 'observed_min': lower, 'observed_max': upper, 'test_value': value, 'reference': 'two_synthesis_examples'}
                            if op_id in ('V03', 'V04'):
                                assert value == param['desired_length'] and value > upper
                            if op_id == 'S01':
                                regime['observed_range_position']['marker'] = template['marker']
                        if op_id == 'V05':
                            assert len(expected) == 1
                            regime['partition_location'] = {'value': 'Boundary', 'attribute': 'target_length', 'boundary': 1, 'requirement': 'nonempty_selected_field'}
                        assertions = [{'assertion_id': oid + '-exact', 'expectation': 'Exact Output', 'expected_output': expected}]
                        if relation:
                            assertions.append({'assertion_id': oid + '-relation', 'base_id': bid, **relation})
                        row.update(status='planned', case_id=cid, regime=regime, input_edit=edit, assertions=assertions, successful_trial=trial, rejected_proposals=dict(rejected))
                        found = True
                        break
                    if not found:
                        row.update(status='unresolved', reason='bounded_generator_found_no_fresh_valid_variant', rejected_proposals=dict(rejected), attempts=TRIALS)
        for op_id in OPERATORS:
            rows = [r for r in task_obligations if r['operator_id'] == op_id]
            statuses = Counter((r['status'] for r in rows))
            applicability.append({'task_id': tid, 'operator_id': op_id, 'obligations': len(rows), 'statuses': dict(statuses), 'unique_cases': len({r['case_id'] for r in rows if r['status'] == 'planned'}), 'reasons': dict(Counter((r['reason'] for r in rows if 'reason' in r)))})
    return {'cases': list(cases.values()), 'obligations': obligations, 'bases': bases, 'applicability': applicability}
