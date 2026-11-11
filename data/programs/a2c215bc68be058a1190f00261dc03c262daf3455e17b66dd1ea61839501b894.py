import re

def transform(x: str) -> str:
    words = re.findall(r"[A-Za-z]+", x)
    if not words:
        return ""
    return max(words, key=len)