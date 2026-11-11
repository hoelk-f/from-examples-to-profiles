import re

def transform(x: str) -> str:
    pattern = re.compile(r'\b[A-Z]{1,2}[0-9][0-9A-Z]?\s[0-9][A-Z]{2}\b', re.I)
    match = pattern.search(x)
    return match.group(0) if match else ""