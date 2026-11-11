import re

def transform(x: str) -> str:
    m = re.search(r'(\d+)\s+Lips', x)
    return m.group(1) if m else ""