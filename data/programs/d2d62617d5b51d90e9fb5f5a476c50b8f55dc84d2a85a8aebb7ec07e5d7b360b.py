import re

def transform(x: str) -> str:
    match = re.search(r'\[\[[^\]|]*\|([^]]+)\]\]', x)
    return match.group(1) if match else ""