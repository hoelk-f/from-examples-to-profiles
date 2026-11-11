import re

def transform(x: str) -> str:
    m = re.search(r'(\w+)\s+[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\s*$', x)
    if m:
        return m.group(1)
    return x
