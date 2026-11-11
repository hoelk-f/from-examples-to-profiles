import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[(.+?)\]\]''", x)
    if m:
        link = m.group(1)
        if '|' in link:
            return link.split('|')[-1]
        return link
    return x
