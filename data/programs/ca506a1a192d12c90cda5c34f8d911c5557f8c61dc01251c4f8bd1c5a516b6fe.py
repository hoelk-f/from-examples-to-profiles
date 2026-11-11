import re

def transform(x: str) -> str:
    m = re.search(r'(\d+\.\d+) CPU in', x)
    return m.group(1)
