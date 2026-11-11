import re

def transform(x: str) -> str:
    m = re.search(r'\d (\d{4}(?:, \d{4})*)$', x)
    return m.group(1)
