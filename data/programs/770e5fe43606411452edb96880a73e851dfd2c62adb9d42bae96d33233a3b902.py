import re

def transform(x: str) -> str:
    m = re.search(r'(\d{4}(?:, \d{4})*)$', x)
    return m.group(1) if m else x
