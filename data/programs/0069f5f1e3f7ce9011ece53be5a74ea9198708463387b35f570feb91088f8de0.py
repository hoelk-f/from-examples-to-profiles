import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^\]]+)\]\]''", x)
    if m:
        val = m.group(1)
        if '|' in val:
            val = val.split('|')[-1]
        return val
    return x
