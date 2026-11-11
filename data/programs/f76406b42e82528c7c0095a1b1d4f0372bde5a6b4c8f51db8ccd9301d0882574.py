import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[(.+?)\]\]''", x)
    if m:
        content = m.group(1)
        if '|' in content:
            return content.split('|')[-1]
        return content
    return x
