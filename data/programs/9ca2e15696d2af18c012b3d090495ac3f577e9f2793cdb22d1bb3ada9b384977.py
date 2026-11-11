import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^]]+)\]\]''", x)
    if not m:
        return ""
    inner = m.group(1)
    return inner.split("|")[-1].strip()