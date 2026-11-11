import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^\]]+)\]\]''", x)
    if m:
        inner = m.group(1)
        if '|' in inner:
            return inner.split('|')[-1]
        return inner
    return x
