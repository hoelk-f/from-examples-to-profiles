import re

def transform(x: str) -> str:
    m = re.match(r'^\d+\s+(.+?)\s+\([A-Z]{3}\)$', x.strip())
    return m.group(1) if m else x