import re

def transform(x: str) -> str:
    match = re.search(r'[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+', x)
    return match.group() if match else x
