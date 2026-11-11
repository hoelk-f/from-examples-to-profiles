import re

def transform(x: str) -> str:
    words = x.strip().split()
    if not words:
        return ""
    last = words[-1]
    # Remove trailing punctuation or non‑alphanumeric characters
    last = re.sub(r'[^0-9A-Za-z]+$', '', last)
    return last