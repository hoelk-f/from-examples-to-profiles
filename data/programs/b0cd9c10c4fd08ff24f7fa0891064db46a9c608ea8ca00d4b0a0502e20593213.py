import re

def transform(x: str) -> str:
    matches = re.findall(r'\[\[[^\]|]+\|([^\]]+)\]\]', x)
    return matches[0]
