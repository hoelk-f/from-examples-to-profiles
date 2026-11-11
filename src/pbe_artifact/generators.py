from collections import Counter, defaultdict
import hashlib
import random
import re
import string
from pbe.behavioral import markers, mutable_runs, same_skeleton, structure_template, prefix_length
from pbe import contract
from pbe.contract import extract, OutsideContract
from pbe.reference_check import evaluate, Invalid
from .common import ROOT, task, read
PLAN = {'random': {'sampling_repetitions': 10}}


def selection_inputs(tid):
    data = task(tid)
    protocol = read(ROOT/'data/selection/protocol.json')
    templates = [r for r in read(ROOT/'data/selection/generation_templates.json') if r['task_id']==tid]
    forbidden = {e['input'][0] for e in data['examples']}
    forbidden.update(c['input'] for c in data['behavioral']['cases'])
    forbidden.update(c['input'] for c in read(ROOT/'data/random'/f'{tid}.json')['cases'])
    records, diagnostics = [], []
    for scenario in templates:
        sid = scenario['scenario']
        memberships, draws = [], []
        for draw in range(1,6):
            namespace = protocol['evaluation_inputs']['seed_namespace'].format(task=tid,scenario=sid,draw=draw)
            rng = random.Random(int(hashlib.sha256(namespace.encode()).hexdigest(),16))
            accepted, rejected, attempts = set(), Counter(), 0
            while len(accepted)<20 and attempts<10000:
                attempts+=1
                value,reason = propose(data,rng.choice(scenario['templates']),rng)
                if reason:
                    rejected[reason]+=1
                    continue
                text=value['input']
                if text in forbidden:
                    rejected['previously_observed_input']+=1
                    continue
                if text in accepted:
                    rejected['duplicate_within_draw']+=1
                    continue
                if sid in ('K','I') and value['expected']!=value['base_expected']:
                    rejected['scenario_invariance']+=1
                    continue
                widths=[len(e['output']) for e in data['split']['training']]
                if sid=='L' and min(widths)<=len(value['expected'])<=max(widths):
                    rejected['scenario_extrapolation']+=1
                    continue
                accepted.add(text)
                cid=tid+'-SEL-'+hashlib.sha256(text.encode()).hexdigest()[:24]
                memberships.append(dict(task_id=tid,scenario=sid,draw=draw,case_id=cid,**value))
            draws.append(dict(draw=draw,seed_namespace=namespace,accepted=len(accepted),attempts=attempts,rejections=dict(rejected)))
        eligible=all(x['accepted']>=10 for x in draws)
        diagnostics.append(dict(scenario=sid,eligible=eligible,draws=draws,
            reason=None if eligible else 'fewer_than_ten_novel_inputs_in_at_least_one_draw'))
        records.extend(dict(row,eligible=eligible) for row in memberships)
    unique={r['case_id']:{k:r[k] for k in ['case_id','input','expected']} for r in records if r['eligible']}
    return dict(task_id=tid,scenarios=diagnostics,memberships=records,execution_cases=list(unique.values()),forbidden_input_count=len(forbidden))


def verify_generated(suite, selected=None):
    from pbe.behavioral import generate as targeted
    from pbe.validation import normalized
    tids=[selected] if selected else read(ROOT/'data/cohort.json')['task_ids']
    for number,tid in enumerate(tids,1):
        data=task(tid)
        if suite in ('behavioral','all'):
            actual=targeted([data],unique_variants=True)
            for field in ['cases','bases','obligations']:
                if [normalized(x) for x in actual[field]]!=data['behavioral'][field]:
                    raise ValueError('Behavioral generator differs for '+tid+' '+field)
        if suite in ('random','all'):
            actual,rejected=generate(tid)
            if actual!=read(ROOT/'data/random'/f'{tid}.json')['cases']:
                raise ValueError('Random generator differs for '+tid)
        if suite in ('selection','all'):
            if selection_inputs(tid)!=read(ROOT/'data/selection/inputs'/f'{tid}.json'):
                raise ValueError('Scenario generator differs for '+tid)
        if number%20==0 or number==len(tids):
            print('Generated inputs match for',number,'of',len(tids),'tasks.',flush=True)


def sample_input(t, generator, rng):
    example = rng.choice(t['split']['training'])
    x = example['input']
    selector = t['parameters']['selector']
    literals = markers(selector)
    changes = []
    for a, b in mutable_runs(x, literals):
        sample = x[a:b]
        length = b - a if generator == 'nominal' else rng.randint(1, 4 * (b - a))
        alphabet = string.digits if sample[0].isdigit() else string.ascii_uppercase if sample[0].isupper() else string.ascii_lowercase
        replacement = ''.join(rng.choice(alphabet) for _ in range(length))
        changes.append((a, b, replacement))
    altered = x
    for a, b, replacement in sorted(changes, reverse=True):
        altered = altered[:a] + replacement + altered[b:]
    if not same_skeleton(x, altered, literals, generator == 'nominal'):
        return None, 'changed_protected_marker'
    template = structure_template(selector)
    if generator == 'broad' and template:
        additions = rng.randint(0, 2)
        maximum = max(len(e['output']) for e in t['split']['training'])
        sample = next((c for c in example['output'] if c.isascii() and c.isalnum()), 'a')
        alphabet = string.digits if sample.isdigit() else string.ascii_uppercase if sample.isupper() else string.ascii_lowercase
        for _ in range(additions):
            dummy = ''.join(rng.choice(alphabet) for _ in range(rng.randint(1, 4 * maximum)))
            if any(marker in dummy for marker in literals):
                return None, 'new_marker_in_dummy'
            before = rng.choice([True, False])
            if template['kind'] == 'marked_block':
                block = template['marker'] + dummy + template['closing_marker']
                altered = block + altered if before else altered + block
            else:
                altered = dummy + template['marker'] + altered if before else altered + template['marker'] + dummy
    if len(altered) > 4096:
        return None, 'input_length_cap'
    return altered, None

def generate(tid):
    t = task(tid)
    n = len(t['behavioral']['cases'])
    assert n > 0
    original = {e['input'][0] for e in t['examples']}
    cases = []
    rejected = Counter()
    for generator in ['nominal', 'broad']:
        for repeat in range(1, PLAN['random']['sampling_repetitions'] + 1):
            seed = f'random-v1:20261031:{generator}:{repeat}:{tid}'
            rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
            accepted = set()
            attempts = 0
            while len(accepted) < n:
                attempts += 1
                if attempts > 100000:
                    raise RuntimeError(f'Insufficient fresh inputs: {tid} {generator} {repeat} {len(accepted)}/{n}')
                text, reason = sample_input(t, generator, rng)
                if reason:
                    rejected[reason] += 1
                    continue
                if text in original or text in accepted:
                    rejected['source_or_suite_duplicate'] += 1
                    continue
                try:
                    expected, span = extract(text, t['parameters']['selector'])
                except OutsideContract:
                    try:
                        evaluate(text, t['parameters']['selector'])
                    except Invalid:
                        rejected['outside_contract'] += 1
                        continue
                    raise AssertionError('Reference validity disagreement')
                assert (expected, span) == evaluate(text, t['parameters']['selector'])
                assert text[span[0]:span[1]] == expected and expected
                accepted.add(text)
                cases.append({'case_id': f'{tid}-{generator}-R{repeat}-{len(accepted)}', 'suite': generator,
                    'sampling_repeat': repeat, 'input': text, 'expected': expected})
    return cases, dict(rejected)

def checked(text, selector):
    outcomes = []
    for function, invalid in [(contract.extract, contract.OutsideContract), (evaluate, Invalid)]:
        try:
            outcomes.append(function(text, selector))
        except invalid:
            outcomes.append(None)
    assert outcomes[0] == outcomes[1], ('Oracle disagreement', text, selector, outcomes)
    return outcomes[0]

def alphabet(char):
    assert char.isascii() and char.isalnum()
    return string.digits if char.isdigit() else string.ascii_uppercase if char.isupper() else string.ascii_lowercase

def propose(task, template, rng):
    selector = task['parameters']['selector']
    bases = {b['base_id']: b for b in task['behavioral']['bases']}
    base = bases[template['base_id']]
    x, y = base['input'], base['expected_output']
    original = checked(x, selector)
    assert original and original[0] == y
    left, right = original[1]
    protected = markers(selector)
    runs = mutable_runs(x, protected)
    op = template['operator']
    edit = {'operator': op, 'base_id': template['base_id'], 'parent_case_id': template['case_id']}
    expected = None
    if op == 'S01':
        shape = structure_template(selector)
        assert shape
        maximum = max(len(e['output']) for e in task['split']['training'])
        sample = next((c for c in y if c.isascii() and c.isalnum()), 'a')
        dummy = ''.join(rng.choice(alphabet(sample)) for _ in range(rng.randint(1, 4 * maximum)))
        if any(m in dummy for m in protected):
            return None, 'new_protected_marker'
        side = template['side']
        if shape['kind'] == 'marked_block':
            block = shape['marker'] + dummy + shape['closing_marker']
            altered = block + x if side == 'before' else x + block
        else:
            altered = dummy + shape['marker'] + x if side == 'before' else x + shape['marker'] + dummy
        edit.update(side=side, dummy=dummy, shape=shape)
    elif op == 'V05':
        assert re.fullmatch('[A-Za-z0-9]+', y)
        replacement = rng.choice(alphabet(y[0]))
        altered = x[:left] + replacement + x[right:]
        expected = replacement
        edit.update(start=left, end=right, replacement=replacement, target_length=1)
    else:
        assert op in ('V02', 'V03', 'V04')
        choices = [(a, b) for a, b in runs if
                   ((b <= left or a >= right) if op == 'V02' else
                    (b <= left if op == 'V03' else left <= a < b <= right))]
        if not choices:
            return None, 'no_mutable_run'
        a, b = rng.choice(choices)
        if op == 'V02':
            replacement = ''.join(rng.choice(alphabet(ch)) for ch in x[a:b])
        else:
            if op == 'V04':
                observed = [len(e['output']) for e in task['split']['training']]
                current = len(y)
            else:
                observed = [prefix_length(e['input'], checked(e['input'], selector)[1], protected)
                            for e in task['split']['training']]
                current = prefix_length(x, original[1], protected)
            maximum = max(observed)
            assert maximum >= 1
            desired = rng.randint(maximum + 1, 4 * maximum)
            extra = ''.join(rng.choice(alphabet(x[b - 1])) for _ in range(desired - current))
            replacement = x[a:b] + extra
            edit.update(desired_length=desired, demonstrated_min=min(observed), demonstrated_max=maximum)
        altered = x[:a] + replacement + x[b:]
        expected = y if op in ('V02', 'V03') else y[:a - left] + replacement + y[b - left:]
        edit.update(start=a, end=b, replacement=replacement)
    if len(altered) > 4096:
        return None, 'length_cap'
    if op != 'S01' and not same_skeleton(x, altered, protected, op == 'V02'):
        return None, 'changed_protected_skeleton'
    oracle = checked(altered, selector)
    if oracle is None:
        return None, 'outside_contract'
    output, span = oracle
    assert output and altered[span[0]:span[1]] == output
    if expected is not None and output != expected:
        return None, 'operator_postcondition'
    if op == 'V03' and prefix_length(altered, span, protected) != edit['desired_length']:
        return None, 'prefix_length_postcondition'
    if op == 'V04' and len(output) != edit['desired_length']:
        return None, 'field_length_postcondition'
    return {'input': altered, 'expected': output, 'expected_span': list(span), 'base_expected': y, 'edit': edit}, None
