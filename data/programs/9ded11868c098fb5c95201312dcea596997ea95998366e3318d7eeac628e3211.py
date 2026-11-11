import re

def transform(x: str) -> str:
    m = re.search(r'\b\d+\s+posts\b', x)
    return m.group(0) if m else ""