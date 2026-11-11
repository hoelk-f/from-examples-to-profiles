import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[([^\]]+)\]\]''", x)
    if m:
        text = m.group(1)
        if '|' in text:
            return text.split('|')[-1]
        return text
    return x
