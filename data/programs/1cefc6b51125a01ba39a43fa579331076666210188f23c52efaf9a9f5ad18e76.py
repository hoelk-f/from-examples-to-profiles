import re

def transform(x: str) -> str:
    match = re.search(r'([\d.]+) CPU in', x)
    return match.group(1)
