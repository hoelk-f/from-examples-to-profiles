import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[(.+?)\]\]''", x)
    inner = m.group(1)
    return inner.split("|")[-1]
