import re

def transform(x: str) -> str:
    m = re.search(r' ([A-Z]{2}), Italy$', x)
    return m.group(1)
