"""Explicit formats and grammar checks for the strict STRING adaptation."""
from pathlib import Path
import hashlib
import json
from .smt_transport import parse_all, render, String, conforms

from pbe.io import repository, write
ROOT = repository() / 'runtimes/hysynth'


class AdapterError(RuntimeError):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def save(path, obj):
    write(path, obj)


def task_parts(text, native=False):
    forms = parse_all(text, native=native)
    synths = [f for f in forms if isinstance(f, list) and f and f[0] == 'synth-fun']
    if len(synths) != 1:
        raise AdapterError('Exactly one synthesis function required')
    synth = synths[0]
    if synth[1:4] != ['f', [['x', 'String']], 'String']:
        raise AdapterError('Only f(x: String): String supported')
    return forms, synth


def rules(text, native=False):
    _, synth = task_parts(text, native)
    result = {name: productions for name, sort, productions in synth[4]}
    if len(result) != len(synth[4]):
        raise AdapterError('Duplicate nonterminal')
    return result


def require_aligned_grammar(text):
    forms, synth = task_parts(text)
    declarations = synth[4]
    if [(d[0], d[1]) for d in declarations] != [('S', 'String'), ('I', 'Int'), ('B', 'Bool')]:
        raise AdapterError('Exactly one productive nonterminal per supported type required')
    r = rules(text)
    for name, sort, productions in declarations:
        for p in productions:
            if isinstance(p, str) and p in r:
                raise AdapterError('Nonterminal aliases are not supported')
            if isinstance(p, list) and (not p or any(not isinstance(c, str) or c not in r for c in p[1:])):
                raise AdapterError('Only flat typed productions supported')
    constraints = [f for f in forms if isinstance(f, list) and f and f[0] == 'constraint']
    return len(constraints)


def unify_legacy(text):
    """Make the prompt equal to the pinned searcher's already type-based space."""
    forms, synth = task_parts(text)
    by_name = {d[0]: d for d in synth[4]}
    if set(by_name) != {'S', 'C', 'I', 'B'} or by_name['C'][1] != 'String':
        raise AdapterError('Unexpected legacy grammar')
    if not all(isinstance(p, String) for p in by_name['C'][2]):
        raise AdapterError('Legacy C must contain literals only')

    def replace(value):
        if value == 'C':
            return 'S'
        if isinstance(value, list):
            return [replace(v) for v in value]
        return value

    string_productions = []
    for production in by_name['S'][2]:
        string_productions.extend(by_name['C'][2] if production == 'C' else [replace(production)])
    synth[4] = [['S', 'String', string_productions]] + [
        [name, by_name[name][1], [replace(p) for p in by_name[name][2]]] for name in ['I', 'B']]
    answer = '\n'.join(render(f) for f in forms)+'\n'
    require_aligned_grammar(answer)
    return answer


def classify(raw, grammar):
    """No code-fence stripping, repair, resampling or example-fit filtering."""
    if not isinstance(raw, str):
        raise AdapterError('Completion text must be a string')
    if len(raw) > 200_000:
        return {'status': 'response_too_large'}
    try:
        terms = parse_all(raw)
    except (ValueError, RecursionError) as error:
        return {'status': 'syntax_invalid', 'detail': str(error)[:500]}
    if len(terms) != 1:
        return {'status': 'syntax_invalid', 'detail': 'Exactly one expression required'}
    if not conforms(terms[0], rules(grammar)):
        return {'status': 'outside_grammar'}
    try:
        native = render(terms[0], native=True)
    except ValueError as error:
        return {'status': 'unsupported_native_literal', 'detail': str(error)}
    if parse_all(native, native=True) != terms:
        raise AdapterError('Literal bridge changed the expression')
    return {'status': 'grammar_valid', 'native_expression': native,
            'canonical_expression': render(terms[0])}


def validate_final(native_expression, grammar):
    try:
        terms = parse_all(native_expression, native=True)
    except (ValueError, RecursionError) as error:
        raise AdapterError('Search returned invalid syntax') from error
    if len(terms) != 1 or not conforms(terms[0], rules(grammar)):
        raise AdapterError('Final candidate violates the exact prompted grammar')
    return render(terms[0], native=True)+'\n'


def verify_seal(root, filename='prepared_hashes.json'):
    for rel, expected in read(Path(root)/filename).items():
        if sha(Path(root)/rel) != expected:
            raise AdapterError('Changed prepared file: '+rel)
