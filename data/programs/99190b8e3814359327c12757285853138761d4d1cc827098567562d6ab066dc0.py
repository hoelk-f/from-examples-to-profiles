import re

def transform(x: str) -> str:
    # Find the first occurrence of ''[[ ... ]]'' pattern
    match = re.search(r"''\[\[(.*?)\]\]''", x)
    if not match:
        return ""
    inner = match.group(1)
    # If there is a pipe, take the part after the last pipe
    if "|" in inner:
        inner = inner.split("|")[-1]
    return inner.strip()