import re

def transform(x: str) -> str:
    m = re.search(r'(\d[\d,]*)\s+Lips', x)
    if not m:
        return ""
    return m.group(1).replace(",", "")