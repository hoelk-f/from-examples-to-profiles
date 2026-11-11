import re

def transform(x: str) -> str:
    m = re.search(r'@(\S+)', x)
    return m.group(1) if m else ""