import re

def transform(x: str) -> str:
    match = re.search(r'(?<!\d)(\d{5})\s*$', x)
    return match.group(1) if match else ''
