import re

def transform(x: str) -> str:
    return re.search(r'([\d.]+) CPU in', x).group(1)
