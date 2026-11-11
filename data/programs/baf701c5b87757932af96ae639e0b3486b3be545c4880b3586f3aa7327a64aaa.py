import re

def transform(x: str) -> str:
    m = re.match(r'^(\d+, .+?)\s+\d+\s+[A-Z]+, France$', x)
    if m:
        return m.group(1)
    return x
