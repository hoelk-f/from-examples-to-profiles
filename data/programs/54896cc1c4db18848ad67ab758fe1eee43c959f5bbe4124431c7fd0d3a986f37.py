import re

def transform(x: str) -> str:
    m = re.match(r'\$([\d.]+)', x)
    return m.group(1)
