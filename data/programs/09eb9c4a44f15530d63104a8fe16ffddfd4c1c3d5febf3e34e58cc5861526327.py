import re

def transform(x: str) -> str:
    return re.sub(r'\s*\(\d{4}\)$', '', x)