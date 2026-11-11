import re

def transform(x: str) -> str:
    match = re.search(r'\d+(?:\.\d+)?g', x)
    return match.group(0) if match else ''