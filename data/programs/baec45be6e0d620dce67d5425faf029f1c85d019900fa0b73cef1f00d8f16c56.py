import re

def transform(x: str) -> str:
    m = re.search(r'([0-9]*\.?[0-9]+) CPU', x)
    return m.group(1) if m else ''