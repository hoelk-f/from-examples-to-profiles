import re

def transform(x: str) -> str:
    m = re.search(r'inferences, (\S+) CPU', x)
    return m.group(1)
