"""Small strict SMT-LIB reader and the explicitly qualified Probe literal bridge."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class String:
    value: str


def parse_all(text, native=False):
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c == ';':
            end = text.find('\n', i)
            i = len(text) if end < 0 else end + 1
        elif c in '()':
            tokens.append(c)
            i += 1
        elif c == '"':
            i += 1
            value = ''
            while True:
                if i >= len(text):
                    raise ValueError('Unterminated string')
                if text[i] == '"':
                    if not native and i + 1 < len(text) and text[i + 1] == '"':
                        value += '"'
                        i += 2
                        continue
                    i += 1
                    break
                if not native and text[i] == '\\':
                    m = re.match(r'\\u(?:\{([0-9a-fA-F]+)\}|([0-9a-fA-F]{4}))', text[i:])
                    if m:
                        value += chr(int(m.group(1) or m.group(2), 16))
                        i += len(m.group())
                        continue
                value += text[i]
                i += 1
            tokens.append(String(value))
        else:
            end = i
            while end < len(text) and not text[end].isspace() and text[end] not in '();"':
                end += 1
            if end == i:
                raise ValueError('Invalid token')
            tokens.append(text[i:end])
            i = end
    def take(pos, depth=0):
        if depth > 100 or pos >= len(tokens):
            raise ValueError('Incomplete or excessively nested expression')
        token = tokens[pos]
        if token == '(':
            values = []
            pos += 1
            while pos < len(tokens) and tokens[pos] != ')':
                value, pos = take(pos, depth + 1)
                values.append(value)
            if pos == len(tokens):
                raise ValueError('Unclosed expression')
            return values, pos + 1
        if token == ')':
            raise ValueError('Unexpected closing parenthesis')
        return token, pos + 1
    result = []
    pos = 0
    while pos < len(tokens):
        value, pos = take(pos)
        result.append(value)
    return result


def render(node, native=False):
    if isinstance(node, String):
        value = node.value
        if native:
            if any(c in value for c in ['"', '\n', '\r']):
                raise ValueError('Unsupported native Probe literal')
        else:
            value = value.replace('\\', '\\u{5c}').replace('"', '""')
        return '"' + value + '"'
    if isinstance(node, list):
        return '(' + ' '.join(render(x, native) for x in node) + ')'
    return node


def to_native(text):
    return '\n'.join(render(node, True) for node in parse_all(text)) + '\n'


def grammar_rules(task_text):
    task = parse_all(task_text)
    synth = next(x for x in task if isinstance(x, list) and x and x[0] == 'synth-fun')
    return {name: productions for name, sort, productions in synth[4]}


def conforms(node, rules, start='S'):
    def matches(value, pattern, depth=0):
        if depth > 150:
            return False
        if isinstance(pattern, str) and pattern in rules:
            return any(matches(value, p, depth+1) for p in rules[pattern])
        if isinstance(pattern, list):
            return isinstance(value, list) and len(value) == len(pattern) and all(matches(v,p,depth+1) for v,p in zip(value,pattern))
        return value == pattern
    return matches(node, start)
