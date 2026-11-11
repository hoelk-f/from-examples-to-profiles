import re

def transform(x: str) -> str:
    tokens = x.split(' ')
    while tokens and re.match(r'^\d[\d,]*$', tokens[-1]):
        tokens.pop()
    return ' '.join(tokens)
