import re

def transform(x: str) -> str:
    pattern = re.compile(r'\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b')
    m = pattern.search(x.upper())
    return m.group(0) if m else ""