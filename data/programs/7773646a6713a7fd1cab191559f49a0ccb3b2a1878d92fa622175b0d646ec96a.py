import re

def transform(x: str) -> str:
    m = re.search(r'\d+\.?\d*g', x)
    return m.group(0) if m else ''
