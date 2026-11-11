import re

def transform(x: str) -> str:
    m = re.search(r'\d+ [A-Z][a-z]{2}', x)
    return m.group(0)
