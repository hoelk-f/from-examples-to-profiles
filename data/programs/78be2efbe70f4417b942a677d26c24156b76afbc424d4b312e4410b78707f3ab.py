import re

def transform(x: str) -> str:
    m = re.search(r'\d+\.?\d*', x)
    return m.group() if m else ''
