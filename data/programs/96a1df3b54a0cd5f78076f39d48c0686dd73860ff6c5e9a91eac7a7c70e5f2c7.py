import re

def transform(x: str) -> str:
    match = re.search(r'\$\d+\.\d{2}', x)
    return match.group(0) if match else x
