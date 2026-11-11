import re

def transform(x: str) -> str:
    match = re.search(r"''\[\[([^]]+)\]\]''", x)
    if not match:
        return ""
    content = match.group(1)
    if "|" in content:
        return content.split("|", 1)[1]
    return content