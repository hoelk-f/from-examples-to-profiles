import re

def transform(x: str) -> str:
    m = re.search(r'\d{4}', x)
    return m.group(0) if m else ''