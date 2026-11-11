import re

def literal(value: str) -> str:
    encoded = []
    for ch in value:
        point = ord(ch)
        if ch == '"':
            encoded.append('""')
        elif ch == '\\' or point < 32 or point > 126:
            encoded.append('\\u{' + format(point, 'x') + '}')
        else:
            encoded.append(ch)
    return '"' + ''.join(encoded) + '"'

def expression(raw: str) -> str:
    tokens = []
    i = 0
    while i < len(raw):
        if raw[i].isspace():
            i += 1
        elif raw[i] in '()':
            tokens.append(raw[i])
            i += 1
        elif raw[i] == '"':
            end = raw.find('"', i + 1)
            if end < 0:
                raise ValueError('Unterminated native string literal')
            tokens.append(literal(raw[i + 1:end]))
            i = end + 1
        else:
            end = i + 1
            while end < len(raw) and (not raw[end].isspace()) and (raw[end] not in '()"'):
                end += 1
            tokens.append(raw[i:end])
            i = end

    def parse(index):
        if index >= len(tokens):
            raise ValueError('Incomplete expression')
        token = tokens[index]
        if token == ')':
            raise ValueError('Unexpected closing parenthesis')
        if token != '(':
            return (token, index + 1)
        parts = []
        index += 1
        while index < len(tokens) and tokens[index] != ')':
            part, index = parse(index)
            parts.append(part)
        if index == len(tokens) or not parts:
            raise ValueError('Invalid expression')
        return ('(' + ' '.join(parts) + ')', index + 1)
    result, end = parse(0)
    if end != len(tokens):
        raise ValueError('Unexpected output after program')
    return result
