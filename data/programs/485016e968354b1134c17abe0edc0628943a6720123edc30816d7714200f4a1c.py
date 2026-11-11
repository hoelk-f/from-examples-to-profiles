import re

def transform(x: str) -> str:
    m = re.search(r'^\d+\s+(.*?)\s+\([A-Z]{3}\)$', x)
    return m.group(1) if m else x