import re

def transform(x: str) -> str:
    pattern = re.compile(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s\d[A-Z]{2}\b')
    match = pattern.search(x.upper())
    return match.group(0) if match else ""