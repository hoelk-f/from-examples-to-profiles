import re

def transform(x: str) -> str:
    tokens = [t.strip() for t in re.split(r'[;,]', x)]
    tokens = [t for t in tokens if t]
    if not tokens:
        return ""
    max_len = max(len(t) for t in tokens)
    for t in tokens:
        if len(t) == max_len:
            return t
    return ""