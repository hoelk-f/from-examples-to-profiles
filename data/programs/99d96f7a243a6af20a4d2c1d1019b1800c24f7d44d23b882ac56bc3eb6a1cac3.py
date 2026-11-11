import re

def transform(x: str) -> str:
    pattern = re.compile(r'^\d{1,3}(?:,\d{3})+$')
    parts = x.split()
    result = []
    for token in parts:
        if pattern.match(token):
            break
        result.append(token)
    return " ".join(result)