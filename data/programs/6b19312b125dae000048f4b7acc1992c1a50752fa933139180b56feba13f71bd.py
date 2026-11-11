import re

def transform(x: str) -> str:
    for m in re.finditer(r'\(([^)]*)\)', x):
        s = m.group(1)
        if s.isalpha() and s.isupper():
            return s
    return ""