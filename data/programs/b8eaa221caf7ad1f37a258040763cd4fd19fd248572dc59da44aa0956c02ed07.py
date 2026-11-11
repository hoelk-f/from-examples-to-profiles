import re

def transform(x: str) -> str:
    match = re.search(r'[A-Z]{1,2}\d[A-Z]?\s?\d[A-Z]{2}$', x)
    return match.group(0) if match else x
