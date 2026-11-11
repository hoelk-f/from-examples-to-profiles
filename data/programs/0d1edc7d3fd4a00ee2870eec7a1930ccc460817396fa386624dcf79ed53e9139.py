import re

def transform(x: str) -> str:
    m = re.search(r'\b(?:AM|PM)\b', x)
    if not m:
        return x.strip()
    return x[:m.end()].strip()