import json

def score(assertion, variant, base=None):
    if variant['status'] != 'returned' or not isinstance(variant['actual'], str):
        return False
    kind = assertion['expectation']
    if kind == 'Exact Output':
        return variant['actual'] == assertion['expected_output']
    if base is None or base['status'] != 'returned' or (not isinstance(base['actual'], str)):
        return False
    if kind == 'Invariance':
        return variant['actual'] == base['actual']
    assert kind == 'Equivariance' and assertion['operation'] == 'replace_slice'
    start, end = (assertion['start'], assertion['end'])
    if not 0 <= start <= end <= len(base['actual']):
        return False
    expected = base['actual'][:start] + assertion['replacement'] + base['actual'][end:]
    return variant['actual'] == expected

def assertion_key(obligation, assertion):
    if assertion['expectation'] == 'Exact Output':
        return ('exact', obligation['case_id'])
    operation = {k: v for k, v in assertion.items() if k not in ('assertion_id', 'base_id')}
    return ('relation', assertion['base_id'], obligation['case_id'], json.dumps(operation, sort_keys=True, ensure_ascii=True))

def cells(obligation, assertion):
    return [(obligation['dimension'], family, item['value'], assertion['expectation']) for family, item in obligation['regime'].items() if 'value' in item]

def controls():
    returned = lambda x: {'status': 'returned', 'actual': x}
    inv = {'expectation': 'Invariance', 'operation': 'identity'}
    exact = {'expectation': 'Exact Output', 'expected_output': '12'}
    eq = {'expectation': 'Equivariance', 'operation': 'replace_slice', 'start': 1, 'end': 2, 'replacement': 'XYZ'}
    checks = [score(inv, returned('wrong'), returned('wrong')) is True, score(exact, returned('wrong')) is False, score(exact, returned('12')) is True, score(exact, returned('12 ')) is False, score(eq, returned('aXYZc'), returned('abc')) is True, score(eq, returned('aXYZc'), returned('a')) is False, score(eq, returned('abc'), returned('abc')) is False, score(inv, {'status': 'execution_error', 'actual': None}, returned('12')) is False, score(exact, {'status': 'non_string_output', 'actual': 12}) is False, score({'expectation': 'Exact Output', 'expected_output': 'é'}, returned('é')) is False]
    assert all(checks)
    o = {'case_id': 'c', 'dimension': 'Value', 'regime': {'contract_conformance': {'value': 'Valid'}, 'distribution_membership': {'status': 'unclear'}}}
    a = {'assertion_id': 'a', **exact}
    b = {'assertion_id': 'b', **exact}
    assert assertion_key(o, a) == assertion_key(o, b)
    assert cells(o, a) == [('Value', 'contract_conformance', 'Valid', 'Exact Output')]
    return {'passed': True, 'scoring_checks': len(checks) + 2, 'study_program_executions': 0}
