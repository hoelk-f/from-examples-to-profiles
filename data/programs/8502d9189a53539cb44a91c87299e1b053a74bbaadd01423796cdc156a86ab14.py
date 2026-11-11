import re

def transform(x: str) -> str:
    match = re.search(r"\b\d{4}\b", x)
    return match.group(0) if match else ""