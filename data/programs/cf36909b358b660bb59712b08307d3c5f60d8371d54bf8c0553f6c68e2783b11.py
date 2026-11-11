import re

def transform(x: str) -> str:
    m = re.search(r'\bask\s+(\S+)', x)
    return m.group(1) if m else ""