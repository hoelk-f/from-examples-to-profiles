import re

def transform(x: str) -> str:
    m = re.match(r'^(.+?)\s+\d+\s+[A-Z]+.*$', x)
    return m.group(1) if m else x
