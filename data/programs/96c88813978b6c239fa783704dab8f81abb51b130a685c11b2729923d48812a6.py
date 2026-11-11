import re

def transform(x: str) -> str:
    m = re.search(r'(\w+)\s+[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}', x)
    return m.group(1) if m else x
