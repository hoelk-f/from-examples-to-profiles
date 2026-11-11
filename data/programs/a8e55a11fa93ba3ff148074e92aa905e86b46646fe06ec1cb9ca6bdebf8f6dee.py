import re

def transform(x: str) -> str:
    pattern = re.compile(r'\b[ A-Z]{1,2}[0-9][0-9A-Z]?\s[0-9][A-Z]{2}\b')
    m = pattern.search(x)
    return m.group(0) if m else ""