import re

def transform(x: str) -> str:
    m = re.search(r'[A-Z]{1,2}\d[A-Z]?\s\d[A-Z]{2}$', x)
    return m.group(0)
