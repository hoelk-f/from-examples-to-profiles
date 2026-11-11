import re

def transform(x: str) -> str:
    m = re.search(r"''\[\[.*?\|(.*?)\]\]''", x)
    return m.group(1)
