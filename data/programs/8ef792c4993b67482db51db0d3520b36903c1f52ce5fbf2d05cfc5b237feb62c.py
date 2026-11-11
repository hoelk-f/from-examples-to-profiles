import re

def transform(x: str) -> str:
    match = re.search(r'\d[\d,]*', x)
    return match.group() if match else ""