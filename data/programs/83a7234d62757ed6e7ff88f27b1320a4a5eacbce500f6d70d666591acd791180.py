import re

def transform(x: str) -> str:
    matches = re.findall(r'\(([^)]*)\)', x)
    for m in matches:
        if m.isupper():
            return m
    return ""
