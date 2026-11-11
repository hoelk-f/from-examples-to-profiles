import re

def transform(x: str) -> str:
    m = re.search(r'([\d.]+) CPU', x)
    return m.group(1) if m else ''