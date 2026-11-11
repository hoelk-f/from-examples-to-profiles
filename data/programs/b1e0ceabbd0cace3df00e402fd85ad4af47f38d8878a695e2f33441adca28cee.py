import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]''", x)
    if m:
        return m.group(2) if m.group(2) else m.group(1)
    return x
