import re

def native_literal(value: str) -> str:
    if '"' in value or value.endswith('\\'):
        raise ValueError('Native literal parser cannot losslessly encode this quote or trailing backslash')
    return '"' + value + '"'

def constants(examples: list[dict]) -> list[str]:
    values = {''}
    for e in examples:
        for value in [e['input'], e['output']]:
            values.update((c for c in value if not c.isalnum()))
            values.update(re.findall('[^\\w]+', value, flags=re.UNICODE))
        values.add(e['output'])
    first = examples[0]['input']
    shared = set()
    for i in range(len(first)):
        for length in range(2, min(24, len(first) - i) + 1):
            part = first[i:i + length]
            if any((not c.isalnum() for c in part)) and all((part in e['input'] for e in examples[1:])):
                shared.add(part)
    maximal = [part for part in shared if not any((part != other and part in other for other in shared))]
    values.update(maximal)
    return sorted(values)

def sygus(examples: list[dict]) -> str:
    vals = ' '.join((native_literal(s) for s in constants(examples)))
    grammar = f'(set-logic SLIA)\n(synth-fun f ((x String)) String\n ((S String (x {vals} (str.++ S S) (str.at S I) (str.substr S I I) (str.replace S C C) (ite B S S)))\n  (C String ({vals}))\n  (I Int (-1 0 1 2 3 4 5 (str.len S) (str.indexof S C I) (+ I I) (- I I)))\n  (B Bool ((str.contains S C) (str.prefixof C S) (str.suffixof C S) (= I I)))))\n'
    for e in examples:
        grammar += f"(constraint (= (f {native_literal(e['input'])}) {native_literal(e['output'])}))\n"
    return grammar + '(check-synth)\n'
