import re

def transform(x: str) -> str:
    m = re.search(r'([A-Z]{2})\s+\d{5}', x)
    return m.group(1)
