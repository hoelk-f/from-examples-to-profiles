import re

def transform(x: str) -> str:
    tokens = x.split(' ')
    while tokens and re.match(r'^\d{1,3}(,\d{3})+$', tokens[-1]):
        tokens.pop()
    return ' '.join(tokens)
