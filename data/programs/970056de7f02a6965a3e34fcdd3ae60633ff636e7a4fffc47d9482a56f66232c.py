import re

def transform(x: str) -> str:
    m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', x)
    return m.group(0) if m else ''