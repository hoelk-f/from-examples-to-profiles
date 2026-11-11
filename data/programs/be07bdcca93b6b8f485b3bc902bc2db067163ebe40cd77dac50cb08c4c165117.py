import re

def transform(x: str) -> str:
    m = re.search(r'\s\d+\s', x)
    if not m:
        return ""
    return x[m.end():].strip()