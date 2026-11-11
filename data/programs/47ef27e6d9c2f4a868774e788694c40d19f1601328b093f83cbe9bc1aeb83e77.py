import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^\]]+)\]\]''", x)
    if m:
        return m.group(1).split("|")[-1]
    return x
