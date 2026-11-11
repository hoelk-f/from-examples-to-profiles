import re

def transform(x: str) -> str:
    match = re.search(r'\d{4}', x)
    return match.group(0) if match else ''
